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

import sys  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench_compat as bc  # noqa: E402  (shared with civ_mcp_hotseat.py)


if os.environ.get("CIV_MCP_BASE_GAME", "1") == "1":
    _PRELUDE = bc.load_prelude()
    _original_execute = GameConnection._execute_and_collect

    async def _base_game_execute(self, state_index, lua_code, timeout):
        return await _original_execute(self, state_index, bc.base_game_rewrite(lua_code, _PRELUDE), timeout)

    GameConnection._execute_and_collect = _base_game_execute
    for _name in bc.XP_TOOLS:
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

    for _name, _rules in bc.OUTPUT_RULES.items():
        _tool = mcp._tool_manager.get_tool(_name)
        if _tool is not None:
            _tool.fn = _filtered(_tool.fn, _rules)
    mcp._tool_manager.get_tool("form_alliance").description += bc.ALLIANCE_NOTE

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

    # A leader screen left open with no diplomacy session stalls the AI turns (bench_compat.LEADER_SCREEN_LUA).
    async def _close_idle_leader_screen(ctx, wait=0.0):
        if wait:
            await asyncio.sleep(wait)  # the engine closes the session a frame later
        try:
            lines = await srv._get_game(ctx).conn.execute_write(bc.LEADER_SCREEN_LUA, timeout=10.0)
        except Exception:
            logging.getLogger("civ_mcp_http").warning("leader screen check failed", exc_info=True)
            return
        if "LEADER_SCREEN|CLOSED" in lines:
            logging.getLogger("civ_mcp_http").info("Closed a leader screen left open with no diplomacy session")
            await asyncio.sleep(1.0)

    def _then_close_leader_screen(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            out = await fn(*args, **kwargs)
            ctx = kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)
            await _close_idle_leader_screen(ctx, wait=1.0)
            return out

        return wrapper

    for _name in ("respond_to_diplomacy", "respond_to_trade"):
        _tool = mcp._tool_manager.get_tool(_name)
        _tool.fn = _then_close_leader_screen(_tool.fn)

    # civ6-mcp warns that InGame queries while the AI civs move can stall their turns, and polls only GameCore then.
    # Two cases reach end_turn while they move: civ6-mcp re-entering a turn end still in flight (after mid-turn
    # diplomacy), and a turn number that advanced before the player's turn started (game 2, turn 145: the agent's
    # moves failed with NO_MOVES, then its end_turn hung until civ6-mcp reloaded the turn).
    _TURN_ACTIVE_LUA = (
        "local p = Players[Game.GetLocalPlayer()] "
        "local ok, a = pcall(function() return p:IsTurnActive() end) "
        "print('ACTIVE|' .. (ok and tostring(a) or 'unknown')) print('---END---')"
    )

    async def _turn_active(game) -> bool | None:
        try:
            lines = await game.conn.execute_read(_TURN_ACTIVE_LUA, timeout=10.0)
        except Exception:
            return None
        flag = next((ln.split("|", 1)[1] for ln in lines if ln.startswith("ACTIVE|")), "unknown")
        return {"true": True, "false": False}.get(flag)

    # The AI civs also wait on a diplomacy session they open with the player mid-turn (game 4, turn 58: civ6-mcp
    # auto-dismissed Brazil's war declaration and reported that the turn had not advanced, but the AI turn was still
    # running, and America then opened a session that waited 20 minutes for an answer nobody was asked for).
    # The player's turn has ended by then, so after the answer the next turn starts: the message must not say "call
    # end_turn again", which would end that turn unplayed (see _pending_turn_report).
    async def _session_waiting(game) -> str | None:
        try:
            sessions = await game.get_diplomacy_sessions()
        except Exception:
            return None
        if not sessions:
            return None
        names = ", ".join(f"{s.other_civ_name} ({s.other_leader_name})" for s in sessions)
        logging.getLogger("civ_mcp_http").info("AI turn waiting on a diplomacy session with %s", names)
        return (f"The AI civs are waiting on you: a diplomacy session with {names} is open. Your turn has already "
                "ended. Read the session with get_pending_diplomacy and answer it with respond_to_diplomacy (or "
                "respond_to_trade for a deal). The AI civs then finish their moves and your next turn starts: play "
                "that turn (get_turn_briefing) before you call end_turn.")

    async def _turn_number(game) -> int | None:
        try:
            lines = await game.conn.execute_read("print('TURN|' .. Game.GetCurrentGameTurn()) print('---END---')",
                                                 timeout=10.0)
        except Exception:
            return None
        return next((int(ln.split("|")[1]) for ln in lines if ln.startswith("TURN|")), None)

    # The diplomacy-pause trap (games 1-6 lost 0 to 14 turns each, tools/turn_trap.py). An AI civ opens a proposal
    # while the AI civs move; civ6-mcp's end_turn stops with "Turn paused ... respond_to_diplomacy, then end_turn
    # again" and keeps its end-turn request in flight (_pending_end_turn). The answer lets the AI civs finish, so the
    # player's next turn starts. The next end_turn is meant to report that turn change, but civ6-mcp first checks
    # end-turn blockers, which now belong to the new turn ("empty queue in Nippur", units needing orders), and reports
    # them as if the old turn were still open. Agents then skipped every unit "to finish the old turn" and lost the
    # new one (game 6, turn 84). While a request is in flight there is nothing to unblock, so that first check is
    # skipped and civ6-mcp reports the turn change, with a line saying whether the new turn still needs playing.
    # Only the first query is skipped: civ6-mcp asks again when the turn fails to advance, and that answer counts.
    import contextvars  # noqa: E402

    from civ_mcp import lua as _lq  # noqa: E402

    _IN_FLIGHT = contextvars.ContextVar("bench_end_turn_in_flight", default=None)
    _original_blocking_query = _lq.build_end_turn_blocking_query

    def _blocking_query():
        skips = _IN_FLIGHT.get()
        if skips and skips[0] > 0:
            skips[0] -= 1
            return f'print("NONE"); print("{_lq.SENTINEL}")'
        return _original_blocking_query()

    _lq.build_end_turn_blocking_query = _blocking_query

    async def _pending_turn_report(fn, args, kwargs) -> str:
        token = _IN_FLIGHT.set([1])
        try:
            out = await fn(*args, **kwargs)
        finally:
            _IN_FLIGHT.reset(token)
        m = re.match(r"Turn (\d+) -> (\d+)", out) if isinstance(out, str) else None
        if m:
            logging.getLogger("civ_mcp_http").info("Reported turn %s -> %s after a diplomacy pause", m[1], m[2])
            out = (f"Turn {m[1]} ended while you answered the AI civ, and this is its report. Your turn {m[2]} is "
                   f"now open. If you have not played it yet, play it now; if you already have, call end_turn again "
                   f"to end it.\n\n" + out)
        return out

    def _units_first(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            ctx = kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)
            game = srv._get_game(ctx)
            if getattr(game, "_pending_end_turn", False):
                return await _pending_turn_report(fn, args, kwargs)  # a turn end in flight: civ6-mcp polls GameCore
            # After a "waiting on you" answer, the first end_turn of the new turn is refused once: the agent may not
            # have seen that its turn changed. Any order or overview since then shows it has (_clears_answered).
            answered = getattr(game, "_bench_answered_at", None)
            if answered is not None:
                game._bench_answered_at = None
                now = await _turn_number(game)
                if now is not None and now > answered and await _turn_active(game):
                    logging.getLogger("civ_mcp_http").info("Refused end_turn of unplayed turn %s", now)
                    return (f"Your turn {now} started after you answered the AI civ, and you have not given any "
                            f"orders in it yet. Play it first (get_turn_briefing), then call end_turn. If you meant "
                            f"to end it without orders, call end_turn again.")
            if await _turn_active(game) is False:
                for i in range(60):  # GameCore polls only, up to 5 minutes
                    if i in (0, 9):  # plus one InGame probe on entry and one at 45 s, as civ6-mcp's own polling does
                        msg = await _session_waiting(game)
                        if msg:
                            game._bench_answered_at = await _turn_number(game)
                            return msg
                    await asyncio.sleep(5)
                    if await _turn_active(game) is not False:
                        logging.getLogger("civ_mcp_http").info("end_turn called before the player's turn started")
                        return ("Your turn had not started yet when you called end_turn: the AI civs were still "
                                "moving, so orders you gave since the last end_turn may have failed (NO_MOVES). It "
                                "has started now. Play this turn (get_turn_briefing), then call end_turn.")
                return ("The AI civs are still moving and your turn has not started after 5 minutes. Call end_turn "
                        "again; give no other orders until it reports the new turn.")
            await _close_idle_leader_screen(ctx)
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

    def _clears_answered(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            ctx = kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)
            if ctx is not None:
                srv._get_game(ctx)._bench_answered_at = None
            return await fn(*args, **kwargs)

        return wrapper

    # get_turn_briefing (defined below) calls get_game_overview and get_units, so it clears the flag too.
    for _name in ("unit_action", "skip_remaining_units", "set_city_production", "set_research", "city_action",
                  "purchase_item", "get_game_overview", "get_units"):
        _tool = mcp._tool_manager.get_tool(_name)
        if _tool is not None:
            _tool.fn = _clears_answered(_tool.fn)

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

# civ6-mcp binds its call log, diary and heartbeat to the game only inside get_game_overview. An agent resumed
# after a server restart can play for turns from end_turn results alone, and until it asks for the overview every
# record waits in memory, untagged by turn (game 1, turns 101-105). Bind on the first call of any tool instead.
_log = logging.getLogger("civ_mcp_http")


async def _bind_game(ctx) -> None:
    lc = ctx.request_context.lifespan_context
    if lc.logger.bound:
        return
    civ, seed = await lc.game.get_game_identity()
    if civ == "unknown":
        return
    lines = await lc.game.conn.execute_read("print('TURN|' .. Game.GetCurrentGameTurn()) print('---END---')")
    turn = next((int(ln.split("|")[1]) for ln in lines if ln.startswith("TURN|")), None)
    if turn is not None:
        lc.logger.set_turn(turn)
        lc.spatial.set_turn(turn)
    lc.logger.bind_game(civ, seed)
    lc.spatial.bind_game(civ, seed)
    srv.heartbeat.bind_game(civ, seed)
    lc.game.spatial = lc.spatial
    _log.info("Bound the call log to %s_%s at turn %s", civ, seed, turn)


def _bound_first(fn):
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        ctx = kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)
        if ctx is not None:
            try:
                await _bind_game(ctx)
            except Exception:  # never block the call itself
                _log.warning("binding the call log failed", exc_info=True)
        return await fn(*args, **kwargs)

    return wrapper


for _tool in mcp._tool_manager.list_tools():
    _tool.fn = _bound_first(_tool.fn)
mcp.settings.host = "127.0.0.1"
mcp.settings.port = int(os.environ.get("CIV_MCP_PORT", "8771"))
mcp.run(transport="streamable-http")
