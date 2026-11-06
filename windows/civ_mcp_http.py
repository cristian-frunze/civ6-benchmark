"""Run civ6-mcp as one long-lived MCP server over streamable HTTP on 127.0.0.1.

Agents reach it through an SSH tunnel (remote/tunnel.sh) and can connect and disconnect (account switches,
restarts) without killing the process. Over SSH stdio, every disconnect killed the server abruptly, and
civ6-mcp warns that an abrupt FireTuner disconnect can crash the game. Run it from the civ6-mcp checkout:
    uv run --extra launcher-windows python civ_mcp_http.py
Env: CIV_MCP_PORT (default 8771), CIV_MCP_BASE_GAME (default 1), plus civ6-mcp's own (CIV_MCP_DISABLE_LUA,
CIV_MCP_AGENT_MODEL, ...).

Two changes to stock civ6-mcp from running it over HTTP instead of stdio:
- The MCP SDK enters the server lifespan once per client session. civ6-mcp's lifespan opens the FireTuner
  connection, and the game accepts only one tuner client at a time (it stops listening while one is
  connected), so a second session could never reach the game. Here the lifespan runs once and every
  session shares it.
- The lifespan also starts a side web API on port 8000 (a second uvicorn). Its shutdown took the main
  server down with it, and nothing here uses it, so it is replaced with a no-op.

Two batch tools cut model round trips, the main cost of a turn (a tool call takes 0.3-1.5 s, a model step
much longer): get_turn_briefing (overview, units, cities and notifications in one call) and issue_orders (a
list of unit, city and research orders in one call). Each inner call still runs and is logged as its own tool.

Three more for the base game (no Rise and Fall or Gathering Storm), on unless CIV_MCP_BASE_GAME=0:
- Each Lua chunk is rewritten to call CB_ names for expansion APIs, with base-game-compat.lua prepended
  (see that file). Tools that read favor, loyalty, eras or World Congress then get neutral values instead
  of failing.
- The tools for systems the base game lacks (governors, dedications, World Congress) are removed.
- Relaunches after a hang use the DX11 exe. civ6-mcp falls back to DX12, which crashes on this laptop.
"""

import asyncio
import contextlib
import functools
import json
import logging
import os
import re
import types

import civ_mcp.game_launcher as launcher
import civ_mcp.server as srv
from civ_mcp.connection import GameConnection
from civ_mcp.server import mcp
from mcp.server.fastmcp import Context

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class _NoWebApi:
    def __init__(self, *args, **kwargs):
        self.should_exit = False

    async def serve(self):
        while not self.should_exit:
            await asyncio.sleep(1)


srv.uvicorn = types.SimpleNamespace(Config=lambda *a, **k: None, Server=_NoWebApi)

_original_lifespan = mcp._mcp_server.lifespan
_shared = {"ctx": None, "stack": None}
_lock = asyncio.Lock()


@contextlib.asynccontextmanager
async def _shared_lifespan(server):
    async with _lock:
        if _shared["ctx"] is None:
            stack = contextlib.AsyncExitStack()
            _shared["ctx"] = await stack.enter_async_context(_original_lifespan(server))
            _shared["stack"] = stack  # never closed: the connection lives as long as the process
    yield _shared["ctx"]


mcp._mcp_server.lifespan = _shared_lifespan

# --- Base game -------------------------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_CB_METHODS = (
    "GetFavor|GetGovernors|GetAllianceType|GetAllianceLevel|GetGrievancesAgainst|GetResourceStockpileCap|"
    "GetResourceAccumulationPerTurn|GetResourceImportPerTurn|GetUnitResourceDemandPerTurn|GetCulturalIdentity|"
    "GetDiplomaticVictoryPoints|GetScienceVictoryPoints|GetScienceVictoryPointsTotalNeeded|GetNextRebelledCity"
)
_XP_TABLES = (
    "Governors|GovernorPromotions|GovernorPromotionSets|GovernorPromotionPrereqs|CommemorationTypes|"
    "Resolutions|Alliances|GovernmentBonuses"
)
_RULES = [
    (re.compile(r":(%s)\(" % _CB_METHODS), r":CB_\1("),
    (re.compile(r"\bGame\.GetEras\(\)"), "CB_ERAS()"),
    (re.compile(r"\bGame\.GetWorldCongress\(\)"), "CB_WC()"),
    (re.compile(r"\bGameInfo\.(%s)\b" % _XP_TABLES), r"(GameInfo.\1 or CB_EMPTY)"),
    # Base-game alliances (one type) unlock with Civil Service; Rise and Fall moved them to Diplomatic Service.
    # Only the alliance checks: the delegation check rightly stays on Diplomatic Service.
    (re.compile(r'local civic = GameInfo\.Civics\["CIVIC_DIPLOMATIC_SERVICE"\]'),
     'local civic = GameInfo.Civics["CIVIC_CIVIL_SERVICE"]'),
    (re.compile(r"Diplomatic Service civic required for alliances"), "Civil Service civic required for alliances"),
    # end_turn sends the end-turn request when UI.CanEndTurn() is true despite blockers, but the base game refuses it
    # while a unit needs orders, and end_turn then polls ~9 minutes (Claude Code gives up after 5) instead of naming
    # the unit. Ask what the game's own end-turn button asks (ActionPanel.lua) so the blocker is reported.
    (re.compile(r"local can = UI\.CanEndTurn\(\);"),
     "local can = UI.CanEndTurn() and NotificationManager.GetFirstEndTurnBlocking(Game.GetLocalPlayer()) "
     "== EndTurnBlockingTypes.NO_ENDTURN_BLOCKING;"),
]
# Lines in tool output that only make sense with the expansions (they would show favor 0 and a golden age
# at era score 0/0).
_OUTPUT_RULES = {
    "get_game_overview": [
        (re.compile(r" \| Favor: [^|\n]*"), ""),
        (re.compile(r"^(Era: [^|\n]+?) \| Score: .*$", re.M), r"\1"),
    ],
    "get_diplomacy": [
        (re.compile(r"Diplomatic Service civic\)"), "Civil Service civic)"),
    ],
    "get_victory_progress": [
        (re.compile(r"launch 4 space projects = 50 VP"), "5 space projects: Earth Satellite, Moon Landing, 3 Mars"),
    ],
}
_XP_TOOLS = [
    "get_governors", "appoint_governor", "assign_governor", "promote_governor",
    "get_dedications", "choose_dedication", "get_world_congress", "queue_wc_votes",
]


def _one_line(lua: str) -> str:
    """The prelude as one line, so line numbers in Lua errors still match civ6-mcp's own code."""
    parts = []
    for line in lua.splitlines():
        line = line.split("--", 1)[0].strip()  # the prelude has no "--" inside strings
        if line:
            parts.append(line)
    return " ".join(parts)


def base_game_rewrite(code: str, prelude: str) -> str:
    new = code
    for rx, rep in _RULES:
        new = rx.sub(rep, new)
    if new == code:
        return code
    return prelude + " " + new


if os.environ.get("CIV_MCP_BASE_GAME", "1") == "1":
    with open(os.path.join(_HERE, "base-game-compat.lua"), encoding="utf-8") as f:
        _PRELUDE = _one_line(f.read())
    _original_execute = GameConnection._execute_and_collect

    async def _base_game_execute(self, state_index, lua_code, timeout):
        return await _original_execute(self, state_index, base_game_rewrite(lua_code, _PRELUDE), timeout)

    GameConnection._execute_and_collect = _base_game_execute
    for _name in _XP_TOOLS:
        mcp._tool_manager.remove_tool(_name)

    def _filtered(fn, rules):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            out = await fn(*args, **kwargs)
            if isinstance(out, str):
                for rx, rep in rules:
                    out = rx.sub(rep, out)
            return out

        return wrapper

    for _name, _rules in _OUTPUT_RULES.items():
        _tool = mcp._tool_manager.get_tool(_name)
        _tool.fn = _filtered(_tool.fn, _rules)
    mcp._tool_manager.get_tool("form_alliance").description += (
        "\n\nBase game: there is one alliance type (alliance_type is ignored), and it needs the Civil Service "
        "civic, not Diplomatic Service."
    )

    # end_turn reads blockers from the notification list, which in the base game can miss a unit that still needs
    # orders (the end-turn button says "Unit needs orders", no notification is listed). It then sends the end turn,
    # the game ignores it, and end_turn waits ~10 minutes before naming the blocker. Ask first what the game's own
    # end-turn button asks (NotificationManager.GetFirstEndTurnBlocking, ActionPanel.lua) and answer at once when
    # units hold the turn. Other blockers go to civ6-mcp, which resolves or reports them.
    _UNITS_BLOCKING_LUA = (
        "local me = Game.GetLocalPlayer() "
        "if NotificationManager.GetFirstEndTurnBlocking(me) == EndTurnBlockingTypes.ENDTURN_BLOCKING_UNITS then "
        "  print('UNITS_BLOCK') "
        "  for _, u in Players[me]:GetUnits():Members() do "
        "    if u:GetX() ~= -9999 and u:GetMovesRemaining() > 0 then "
        "      local e = GameInfo.Units[u:GetType()] "
        "      print('UNIT|' .. u:GetID() .. '|' .. (e and e.UnitType or '?') .. '|' .. u:GetX() .. ',' .. u:GetY() "
        "        .. '|' .. u:GetMovesRemaining() .. '/' .. u:GetMaxMoves()) "
        "    end "
        "  end "
        "end "
        "print('---END---')"
    )

    def _units_first(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            ctx = kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)
            try:
                lines = await srv._get_game(ctx).conn.execute_write(_UNITS_BLOCKING_LUA, timeout=10.0)
            except Exception:
                lines = []
            if "UNITS_BLOCK" in lines:
                units = [ln.split("|") for ln in lines if ln.startswith("UNIT|")]
                if units:
                    listed = "\n".join(f"  {t} [id:{i}] at ({xy}), moves {m}" for _, i, t, xy, m in units)
                    return ("Cannot end turn: a unit still needs orders (the game's end-turn button reads "
                            "\"Unit needs orders\"). Units with moves left:\n" + listed +
                            "\nGive each an order (move, attack, fortify, skip) with unit_action, or call "
                            "skip_remaining_units, then end_turn again. The turn has not ended.")
            return await fn(*args, **kwargs)

        return wrapper

    _tool = mcp._tool_manager.get_tool("end_turn")
    _tool.fn = _units_first(_tool.fn)

    _original_find_exe = launcher._find_game_exe_win32

    def _find_dx11_exe():
        exe = _original_find_exe()
        if exe and exe.endswith("_DX12.exe"):
            dx11 = exe[: -len("_DX12.exe")] + ".exe"
            if os.path.exists(dx11):
                return dx11
        return exe

    launcher._find_game_exe_win32 = _find_dx11_exe

# --- Batch tools ---------------------------------------------------------------------------------------

_BRIEFING = ["get_game_overview", "get_units", "get_cities", "get_notifications"]
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


@mcp.tool(annotations={"readOnlyHint": True})
async def get_turn_briefing(ctx: Context) -> str:
    """Start-of-turn briefing in one call: get_game_overview, get_units, get_cities and get_notifications,
    in that order, each under its own heading. Same output as calling the four tools separately."""
    parts = []
    for name in _BRIEFING:
        parts.append(f"## {name}\n{await _call(name, ctx, {})}")
    return "\n\n".join(parts)


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

    A failed order is reported and the rest still run. Check each result: a move reports the target tile,
    not where the unit ended up.
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
        if name not in _ORDER_TOOLS:
            lines.append(f"{i}. {name}: Error: not allowed here (allowed: {', '.join(_ORDER_TOOLS)})")
            continue
        if not isinstance(args, dict):
            lines.append(f"{i}. {name}: Error: args must be an object")
            continue
        shown = ", ".join(f"{k}={v}" for k, v in args.items())
        lines.append(f"{i}. {name}({shown}): {await _call(name, ctx, args)}")
    return "\n".join(lines)


if os.environ.get("CIV_MCP_DISABLE_LUA"):
    mcp._tool_manager.remove_tool("run_lua")
mcp.settings.host = "127.0.0.1"
mcp.settings.port = int(os.environ.get("CIV_MCP_PORT", "8771"))
mcp.run(transport="streamable-http")
