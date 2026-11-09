"""Offline tests of windows/civ_mcp_http.py's fixes to civ6-mcp: the diplomacy-pause fix, run against civ6-mcp's
real execute_end_turn with a fake game connection, and the menu-load click retry. No game or network needed.

    cd vendor/civ6-mcp && uv run --frozen python ../../tools/tests/test_civ_mcp_http.py
"""
import asyncio, os, shutil, sys, tempfile
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["CIV_MCP_BASE_GAME"] = "1"
# On the PC the Lua prelude sits next to the module, as here.
TMP = tempfile.mkdtemp()
for f in ("windows/civ_mcp_http.py", "windows/bench_compat.py", "lua/base-game-compat.lua"):
    shutil.copy(os.path.join(REPO, f), TMP)
path = os.path.join(TMP, "civ_mcp_http.py")
src = open(path).read()
assert src.count('mcp.run(') == 1
src = src[: src.index("mcp.run(")] + "pass\n"
ns = {"__name__": "civ_mcp_http_test", "__file__": path}
exec(compile(src, path, "exec"), ns)

from civ_mcp import lua as lq
from mcp.server.fastmcp import Context
srv = ns["srv"]
mcp = ns["mcp"]
ORIG_QUERY = ns["_original_blocking_query"]()

class Conn:
    def __init__(self, turn, advance_on_poll=None):
        self.turn, self.active, self.endturn_sent, self.blocker_queries = turn, True, 0, []
        self.advance_on_poll = advance_on_poll
    async def execute_read(self, lua, timeout=None):
        if "IsTurnActive" in lua: return [f"ACTIVE|{str(self.active).lower()}", lq.SENTINEL]
        if "TURN|" in lua: return [f"TURN|{self.turn}", lq.SENTINEL]
        if "GetCurrentGameTurn" in lua:
            if self.advance_on_poll: self.turn = self.advance_on_poll
            return [str(self.turn), lq.SENTINEL]
        if "anyMoves" in lua: return ["UNITS_NEED_ORDERS", lq.SENTINEL]
        return [lq.SENTINEL]
    async def execute_write(self, lua, timeout=None):
        if 'print("NONE")' in lua and "BLOCKING" not in lua:
            self.blocker_queries.append("skipped"); return ["NONE", lq.SENTINEL]
        if lua == ORIG_QUERY:
            self.blocker_queries.append("real")
            return ["BLOCKING|ENDTURN_BLOCKING_UNITS|A unit needs orders", lq.SENTINEL]
        if "UI.CanEndTurn" in lua: return ["CANNOT_END", lq.SENTINEL]
        if "ACTION_ENDTURN" in lua or "EndTurn" in lua: self.endturn_sent += 1
        if "UNITS_BLOCK" in lua: return [lq.SENTINEL]
        return [lq.SENTINEL]

from civ_mcp.game_state import GameState
class Game:
    _build_turn_report = GameState.__dict__["_build_turn_report"]
    def __init__(self, turn, pending_from=None, advance_on_poll=None):
        self.conn = Conn(turn, advance_on_poll)
        self._run_aborted = False
        self._pending_end_turn = pending_from is not None
        self._pending_end_turn_from = pending_from
        self._last_snapshot = None
        self._high_water_turn = 0
        self._last_game_over = None
        self._bench_answered_at = None
    def __getattr__(self, name):
        if name.startswith('_'): raise AttributeError(name)
        async def f(*a, **k):
            if name in ("get_diplomacy_sessions", "get_pending_deals"): return []
            if name == "check_game_over": return None
            if name == "dismiss_popup": return ""
            raise RuntimeError(f"fake: {name}")
        return f

class FakeCtx(Context):
    def __init__(self): pass

GAME = None
srv._get_game = lambda ctx: GAME
CTX = FakeCtx()
from civ_mcp.end_turn import execute_end_turn
async def stock(ctx=None): return await execute_end_turn(GAME)
wrapped = ns["_units_first"](stock)
ok = True
def check(name, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(("PASS" if cond else "FAIL"), name, detail)

async def main():
    global GAME
    import civ_mcp.end_turn as et
    et.asyncio.sleep = (lambda real: (lambda s: real(0)))(asyncio.sleep)  # no real waits
    ns["asyncio"].sleep = et.asyncio.sleep

    # 1. The trap, unfixed: civ6-mcp's own end_turn reports turn 84's unit blocker as if 83 were still open.
    GAME = Game(turn=84, pending_from=83)
    out = await stock()
    check("stock reports the new turn's blockers", out.startswith("Cannot end turn"), repr(out.splitlines()[0]))

    # 2. Through the wrapper: blocker check skipped once, turn change reported, no new end-turn request.
    GAME = Game(turn=84, pending_from=83)
    out = await wrapped(ctx=CTX)
    check("wrapper reports the turn change", out.startswith("Turn 83 ended while you answered"), repr(out[:90]))
    check("report contains civ6-mcp's 83 -> 84 summary", "Turn 83 -> 84" in out)
    check("no ACTION_ENDTURN sent", GAME.conn.endturn_sent == 0, GAME.conn.endturn_sent)
    check("only one blocker query, skipped", GAME.conn.blocker_queries == ["skipped"], GAME.conn.blocker_queries)
    check("pending flag cleared", GAME._pending_end_turn is False)
    check("override scoped to the call", lq.build_end_turn_blocking_query() == ORIG_QUERY)

    # 3. In flight but the turn never advances: the late blocker check runs for real.
    GAME = Game(turn=83, pending_from=83)
    out = await wrapped(ctx=CTX)
    check("late check is real", GAME.conn.blocker_queries == ["skipped", "real"], GAME.conn.blocker_queries)
    check("late check reported", "Blocker: Units" in out, repr(out[:120]))

    # 4. Normal turn, nothing in flight: blockers still reported.
    GAME = Game(turn=84)
    out = await wrapped(ctx=CTX)
    check("normal turn keeps the blocker check", out.startswith("Cannot end turn"), repr(out.splitlines()[0]))

    # 5. Refuse-once guard after a "waiting on you" answer.
    GAME = Game(turn=85); GAME._bench_answered_at = 84
    out = await wrapped(ctx=CTX)
    check("first end_turn of the unplayed turn refused", out.startswith("Your turn 85 started after you answered"), repr(out[:80]))
    check("guard is one-shot", GAME._bench_answered_at is None)
    out = await wrapped(ctx=CTX)
    check("second end_turn goes through", out.startswith("Cannot end turn"), repr(out.splitlines()[0]))

    # 6. Orders and overview clear the flag before end_turn.
    for name in ("unit_action", "skip_remaining_units", "set_city_production", "set_research", "city_action",
                 "purchase_item", "get_game_overview", "get_units"):
        GAME = Game(turn=85); GAME._bench_answered_at = 84
        tool = mcp._tool_manager.get_tool(name)
        try:
            await tool.fn(CTX)
        except Exception:
            pass
        check(f"{name} clears the flag", GAME._bench_answered_at is None)
    GAME = Game(turn=85); GAME._bench_answered_at = 84
    try:
        await mcp._tool_manager.get_tool("get_turn_briefing").fn(CTX)
    except Exception:
        pass
    check("get_turn_briefing clears the flag", GAME._bench_answered_at is None)

    # 7. Same turn after the answer (AI still finishing): not refused.
    GAME = Game(turn=84); GAME._bench_answered_at = 84
    out = await wrapped(ctx=CTX)
    check("no refusal when the turn has not changed", not out.startswith("Your turn"), repr(out.splitlines()[0]))

asyncio.run(main())

# 8. Menu load: a missed "Load Game" clicks "Single Player" again (game 7, turn 102; game 8's start).
import civ_mcp.game_launcher as launcher
def fake_clicks(script):
    calls = []
    def f(target, *a, **k):
        calls.append(target)
        return script.pop(0) if script else False
    return f, calls
ns["_original_click_text"], calls = fake_clicks([False, True, True])  # Load Game missed, Single Player, Load Game
check("missed Load Game retried after a second Single Player click",
      launcher._click_text("Load Game", timeout=5, exact=True, post_delay=0.5, y_offset=15) is True, calls)
check("retry order", calls == ["Load Game", "Single Player", "Load Game"], calls)
ns["_original_click_text"], calls = fake_clicks([False])
check("other targets are not retried", launcher._click_text("Autosaves", timeout=10) is False and calls == ["Autosaves"], calls)
ns["_original_click_text"], calls = fake_clicks([])
check("gives up when Single Player is gone", launcher._click_text("Load Game") is False
      and calls == ["Load Game"] + ["Single Player"] * 3, calls)
ns["_original_click_text"], calls = fake_clicks([False, True, False, True, False, True, False])
check("gives up after 3 retries", launcher._click_text("Load Game") is False and len(calls) == 7, calls)
import inspect
check("civ6-mcp's menu navigation calls the patched _click_text",
      "_click_text(\"Load Game\"" in inspect.getsource(launcher._navigate_to_save_sync)
      and launcher._click_text is ns["_click_text_again"])
shutil.rmtree(TMP, ignore_errors=True)
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
