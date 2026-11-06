"""Run the hotseat fork of civ6-mcp (Johnor12/civ6-mcp) as one MCP server over streamable HTTP, for Opus vs Opus.

FireTuner is off in every multiplayer mode, hotseat included, so this fork drives the game through the MCP Bridge UI
mod (a Lua file the game re-reads every 0.2 s, answers in Lua.log). Each agent plays one hotseat seat: its session is
resumed on its own turn, calls begin_standin_turn(<its leader>), plays, and calls end_turn, which hands the game to the
next seat's turn-change screen (tools/run_hotseat.py does the dispatching). Run it from the fork's checkout:
    uv run python civ_mcp_hotseat.py
Env: CIV_MCP_PORT (default 8771), CIV_MCP_BASE_GAME (default 1).

Changes to the stock fork:
- Base game (no Rise and Fall or Gathering Storm), as in civ_mcp_http.py: Lua sent to the in-game context is
  rewritten to call CB_ stand-ins (bench_compat.py, base-game-compat.lua); the governor, dedication and World Congress
  tools are removed; overview lines about favor and era score are dropped.
- Server instructions for a competitive game instead of standing in for an absent friend.
- A leader screen left open with no diplomacy session is closed after diplomacy replies and before end_turn.
- issue_orders: several unit, city and research orders in one call, as in civ_mcp_http.py.
"""

import asyncio
import functools
import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bench_compat as bc  # noqa: E402
import civ_mcp.bridge as bridge  # noqa: E402
import civ_mcp.server as srv  # noqa: E402
from civ_mcp.server import mcp  # noqa: E402
from mcp.server.fastmcp import Context  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
_log = logging.getLogger("civ_mcp_hotseat")

mcp._mcp_server.instructions = (
    "Civilization VI hotseat game: you play one civilization against other agents and the game's AI. On your turn, "
    "call begin_standin_turn(<your leader>) (its reply is the turn briefing), play the turn, and call end_turn "
    "exactly once. Every game tool acts for the seat whose turn it is."
)


def _ctx_of(args, kwargs):
    return kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)


if os.environ.get("CIV_MCP_BASE_GAME", "1") == "1":
    _PRELUDE = bc.load_prelude()
    _original_write = bridge.BridgeConnection._write_command

    def _base_game_write(self, seq, context, code):
        if context == bridge.CONTEXT_INGAME:
            code = bc.base_game_rewrite(code, _PRELUDE)
        return _original_write(self, seq, context, code)

    bridge.BridgeConnection._write_command = _base_game_write

    for _name in bc.XP_TOOLS:
        if mcp._tool_manager.get_tool(_name) is not None:
            mcp._tool_manager.remove_tool(_name)

    def _filtered(fn, rules):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            out = await fn(*args, **kwargs)
            return bc.filter_output(out, rules) if isinstance(out, str) else out

        return wrapper

    for _name, _rules in bc.OUTPUT_RULES.items():
        _tool = mcp._tool_manager.get_tool(_name)
        if _tool is not None:
            _tool.fn = _filtered(_tool.fn, _rules)
    _tool = mcp._tool_manager.get_tool("form_alliance")
    if _tool is not None:
        _tool.description += bc.ALLIANCE_NOTE


async def _close_idle_leader_screen(ctx, wait=0.0):
    if ctx is None:
        return
    if wait:
        await asyncio.sleep(wait)  # the engine closes the session a frame later
    try:
        lines = await srv._session(ctx).conn.execute(bc.LEADER_SCREEN_LUA, timeout=10.0)
    except Exception:
        _log.warning("leader screen check failed", exc_info=True)
        return
    if "LEADER_SCREEN|CLOSED" in lines:
        _log.info("Closed a leader screen left open with no diplomacy session")
        await asyncio.sleep(1.0)


def _then_close_leader_screen(fn):
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        out = await fn(*args, **kwargs)
        await _close_idle_leader_screen(_ctx_of(args, kwargs), wait=1.0)
        return out

    return wrapper


def _leader_screen_first(fn):
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        await _close_idle_leader_screen(_ctx_of(args, kwargs))
        return await fn(*args, **kwargs)

    return wrapper


for _name in ("respond_to_diplomacy", "respond_to_trade"):
    _tool = mcp._tool_manager.get_tool(_name)
    if _tool is not None:
        _tool.fn = _then_close_leader_screen(_tool.fn)
mcp._tool_manager.get_tool("end_turn").fn = _leader_screen_first(mcp._tool_manager.get_tool("end_turn").fn)

# --- Batch orders ------------------------------------------------------------------------------------------

_ORDER_TOOLS = [
    "unit_action", "skip_remaining_units", "promote_unit", "upgrade_unit",
    "set_city_production", "purchase_item", "purchase_tile", "set_city_focus", "city_action",
    "set_research", "set_policies", "send_envoy",
]


async def _call(name: str, ctx: Context, args: dict) -> str:
    tool = mcp._tool_manager.get_tool(name)
    if tool is None:
        return f"Error: no tool {name}"
    try:
        return str(await tool.fn(ctx, **args))
    except TypeError as e:
        return f"Error: bad arguments for {name}: {e}"
    except Exception as e:  # one failed order shouldn't stop the rest
        return f"Error: {name} failed: {e}"


@mcp.tool()
async def issue_orders(ctx: Context, orders: str) -> str:
    """Run several orders in one call, in the order given, and report each result. Use it for the routine part
    of a turn: unit moves and actions, production, purchases, research and policies.

    Args:
        orders: JSON list of {"tool": <name>, "args": {...}}, where each entry is exactly what you would pass to
            that tool. Allowed tools: unit_action, skip_remaining_units, promote_unit, upgrade_unit,
            set_city_production, purchase_item, purchase_tile, set_city_focus, city_action, set_research,
            set_policies, send_envoy. Example:
            [{"tool": "unit_action", "args": {"unit_id": 65536, "action": "move", "target_x": 40, "target_y": 41}},
             {"tool": "set_city_production", "args": {"city_id": 65536, "item_type": "UNIT", "item_name": "UNIT_SETTLER"}},
             {"tool": "set_research", "args": {"tech_or_civic": "TECH_MINING"}}]

    A failed order is reported and the rest still run. Check each result.
    """
    try:
        items = json.loads(orders)
    except ValueError as e:
        return f"Error: orders is not valid JSON: {e}"
    if not isinstance(items, list) or not items:
        return "Error: orders must be a non-empty JSON list"
    lines = []
    for i, item in enumerate(items, 1):
        name = item.get("tool") if isinstance(item, dict) else None
        args = item.get("args") or {} if isinstance(item, dict) else {}
        if name not in _ORDER_TOOLS or mcp._tool_manager.get_tool(name) is None:
            lines.append(f"{i}. {name}: Error: not allowed here (allowed: {', '.join(_ORDER_TOOLS)})")
            continue
        if not isinstance(args, dict):
            lines.append(f"{i}. {name}: Error: args must be an object")
            continue
        shown = ", ".join(f"{k}={v}" for k, v in args.items())
        lines.append(f"{i}. {name}({shown}): {await _call(name, ctx, args)}")
    return "\n".join(lines)


# --- For the coordinator only (tools/run_hotseat.py removes it from every agent's tool list) ----------------

_STATS_LUA = (
    "local win = -1 pcall(function() win = Game.GetWinningTeam() end) "
    "print('GAME|' .. Game.GetCurrentGameTurn() .. '|' .. tostring(win) .. '|' .. Game.GetLocalPlayer()) "
    "for i = 0, 62 do "
    "  local p = Players[i] local cfg = PlayerConfigurations[i] "
    "  if p and cfg and p:IsMajor() and cfg:GetLeaderTypeName() then "
    "    local alive = p:IsAlive() "
    "    local nc, pop = 0, 0 "
    "    for _, c in p:GetCities():Members() do nc = nc + 1 pop = pop + c:GetPopulation() end "
    "    local st = p:GetStats() "
    "    local f = {i, cfg:GetLeaderTypeName(), Locale.Lookup(cfg:GetCivilizationShortDescription()), "
    "      tostring(alive), tostring(p:IsHuman()), p:GetTeam(), p:GetScore(), nc, pop, "
    "      string.format('%.1f', p:GetTechs():GetScienceYield()), string.format('%.1f', p:GetCulture():GetCultureYield()), "
    "      string.format('%.1f', p:GetTreasury():GetGoldBalance()), st:GetMilitaryStrength(), "
    "      st:GetNumTechsResearched(), st:GetNumCivicsCompleted()} "
    "    for k = 1, #f do f[k] = string.gsub(tostring(f[k]), '|', '/') end "
    "    print('MAJOR|' .. table.concat(f, '|')) "
    "  end "
    "end "
    "print('---END---')"
)
_STAT_KEYS = ["id", "leader", "civ", "alive", "human", "team", "score", "cities", "pop", "science", "culture",
              "gold", "military", "techs", "civics"]


@mcp.tool(annotations={"readOnlyHint": True})
async def bench_stats(ctx: Context) -> str:
    """Benchmark coordinator only: every major civ's score and yields, and the winning team, as JSON."""
    lines = await srv._session(ctx).conn.execute(_STATS_LUA, timeout=15.0)
    out: dict = {"players": []}
    for ln in lines:
        f = ln.split("|")
        if f[0] == "GAME" and len(f) >= 4:
            out.update(turn=int(f[1]), winning_team=int(f[2]), local_player=int(f[3]))
        elif f[0] == "MAJOR" and len(f) == len(_STAT_KEYS) + 1:
            row = dict(zip(_STAT_KEYS, f[1:]))
            for k in ("alive", "human"):
                row[k] = row[k] == "true"
            for k in ("id", "team", "score", "cities", "pop", "military", "techs", "civics"):
                row[k] = int(float(row[k]))
            for k in ("science", "culture", "gold"):
                row[k] = float(row[k])
            out["players"].append(row)
    return json.dumps(out)


@mcp.tool()
async def bench_launch_staged_game(ctx: Context) -> str:
    """Benchmark coordinator only: start the hotseat game waiting in the staging room (made by lua/new-hotseat.lua
    over FireTuner, which stops answering inside the session) and wait for the first turn-change screen."""
    import civ_mcp.hotseat as hs

    conn = srv._session(ctx).conn
    t0 = time.monotonic()
    while True:
        try:
            fe = await hs.frontend_status(conn)
        except Exception:
            fe = hs.HotseatStatus(screen="none")
        if fe.in_session and fe.is_hotseat:
            break
        if time.monotonic() - t0 > 90:
            return f"No hotseat staging room after 90 s: {fe.describe()}"
        await asyncio.sleep(1.0)
    await asyncio.sleep(1.5)
    lines = await conn.execute_in_context(bridge.CONTEXT_FRONTEND, hs._LAUNCH_LUA, 8.0)
    if "LAUNCHED" not in lines:
        return f"Could not start the game from the staging room: {lines}"
    if not await hs.wait_for(conn, "ingame", 300.0):
        return "Timed out waiting for the game to load."
    st = hs.HotseatStatus(screen="none")
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            st = await hs.ingame_status(conn)
        except Exception:
            st = hs.HotseatStatus(screen="none")
        if st.screen == "ingame" and (st.turn_controls_visible or st.turn_active):
            break
        await asyncio.sleep(1.0)
    return f"Started in {int(time.monotonic() - t0)} s. {st.describe()}"


mcp.settings.host = "127.0.0.1"
mcp.settings.port = int(os.environ.get("CIV_MCP_PORT", "8771"))
mcp.run(transport="streamable-http")
