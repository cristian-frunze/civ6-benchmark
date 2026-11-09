"""Offline tests of windows/civ_mcp_http.py's fixes to civ6-mcp: the diplomacy-pause fix and the dropped end-turn
request, run against civ6-mcp's real execute_end_turn with a fake game connection; the diplomacy screen left locked
by trades; the note after a hang reload; the move-and-attack result; and the menu-load click retry. No game or
network needed.

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
        self.advance_on_poll = advance_on_poll  # the turn number once an end-turn request was sent
        self.blockers = True  # the real blocker query answers "a unit needs orders"
        self.view = "hidden"  # the diplomacy screen: hidden, visible (one close works) or stuck (never closes)
        self.leader_checks, self.writes = 0, []
    async def execute_read(self, lua, timeout=None):
        if "IsTurnActive" in lua: return [f"ACTIVE|{str(self.active).lower()}", lq.SENTINEL]
        if "TURN|" in lua: return [f"TURN|{self.turn}", lq.SENTINEL]
        if "GetCurrentGameTurn" in lua:
            if self.advance_on_poll and self.endturn_sent: self.turn = self.advance_on_poll
            return [str(self.turn), lq.SENTINEL]
        if "anyMoves" in lua: return ["UNITS_NEED_ORDERS", lq.SENTINEL]
        return [lq.SENTINEL]
    async def execute_write(self, lua, timeout=None):
        self.writes.append(lua)
        if "LEADER_SCREEN|" in lua:
            self.leader_checks += 1
            if self.view == "hidden": return ["LEADER_SCREEN|HIDDEN", lq.SENTINEL]
            if self.view == "visible": self.view = "hidden"
            return ["LEADER_SCREEN|CLOSED", lq.SENTINEL]
        if 'print("NONE")' in lua and "BLOCKING" not in lua:
            self.blocker_queries.append("skipped"); return ["NONE", lq.SENTINEL]
        if lua == ORIG_QUERY:
            self.blocker_queries.append("real")
            if not self.blockers: return [lq.SENTINEL]
            return ["BLOCKING|ENDTURN_BLOCKING_UNITS|A unit needs orders", lq.SENTINEL]
        if "UI.CanEndTurn" in lua: return ["CANNOT_END", lq.SENTINEL]
        if "UNITS_BLOCK" in lua: return [lq.SENTINEL]
        if "ACTION_ENDTURN" in lua: self.endturn_sent += 1
        if "build_propose_trade" in lua or "SendWorkingDeal" in lua: return ["OK:ACCEPTED|Trade accepted with Spain", lq.SENTINEL]
        return [lq.SENTINEL]

from civ_mcp.game_state import GameState
class Game:
    _build_turn_report = GameState.__dict__["_build_turn_report"]
    propose_trade = GameState.__dict__["propose_trade"]  # the wrapper's version
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
class FakeLogger:
    _turn = 1
    def __getattr__(self, name):
        async def f(*a, **k): return None
        return f
srv._get_logger = lambda ctx: FakeLogger()
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

    # 3. In flight (the player's turn is inactive: the AI civs move) but the turn never advances: the late blocker
    #    check runs for real.
    GAME = Game(turn=83, pending_from=83); GAME.conn.active = False
    out = await wrapped(ctx=CTX)
    check("late check is real", GAME.conn.blocker_queries == ["skipped", "real"], GAME.conn.blocker_queries)
    check("late check reported", "Blocker: Units" in out, repr(out[:120]))
    check("no new request while the AI civs move", GAME.conn.endturn_sent == 0, GAME.conn.endturn_sent)

    # 3b. The request was dropped (first contact, game 8 turn 13): same turn number, the player's turn active again.
    #     A new request is sent and the turn ends.
    GAME = Game(turn=83, pending_from=83, advance_on_poll=84); GAME.conn.blockers = False
    out = await wrapped(ctx=CTX)
    check("dropped request: a new one is sent", GAME.conn.endturn_sent == 1, GAME.conn.endturn_sent)
    check("dropped request: the turn ends", out.startswith("Turn 83 -> 84"), repr(out[:80]))
    check("dropped request: no 'ended while you answered' line", "while you answered" not in out)
    check("dropped request: blocker check not skipped", GAME.conn.blocker_queries == ["real"], GAME.conn.blocker_queries)

    # 3c. Dropped request but a unit still needs orders: the blocker is reported, nothing is sent.
    GAME = Game(turn=83, pending_from=83)
    out = await wrapped(ctx=CTX)
    check("dropped request with a blocker: reported", out.startswith("Cannot end turn"), repr(out.splitlines()[0]))
    check("dropped request with a blocker: nothing sent", GAME.conn.endturn_sent == 0)

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

    # 9. Trades: propose_trade no longer hides the diplomacy screen (that kept its engine lock), and the
    #    leader-screen check closes it after the trade.
    check("GameState.propose_trade replaced", GameState.propose_trade is ns["_propose_trade_no_hide"])
    tool = mcp._tool_manager.get_tool("propose_trade")
    GAME = Game(turn=207); GAME.conn.view = "visible"
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("trade result passed through", out.startswith("ACCEPTED"), repr(out[:60]))
    check("no SetHide of the diplomacy screen", not any("SetHide" in w for w in GAME.conn.writes))
    check("screen closed after the trade", GAME.conn.view == "hidden" and GAME.conn.leader_checks == 2,
          (GAME.conn.view, GAME.conn.leader_checks))
    GAME = Game(turn=207); GAME.conn.view = "stuck"
    await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("a screen that will not close: 3 attempts", GAME.conn.leader_checks == 3, GAME.conn.leader_checks)
    # Every tool's outermost wrapper binds the call log (_bound_first); the one inside it is checked.
    bound = ns["_bound_first"](stock).__code__
    for name in ("respond_to_diplomacy", "respond_to_trade", "propose_trade", "send_diplomatic_action",
                 "propose_peace", "form_alliance"):  # test_trade is propose_trade(mode="test")
        fn = mcp._tool_manager.get_tool(name).fn
        check(f"{name} closes the screen after", fn.__code__ is bound
              and fn.__wrapped__.__code__ is ns["_then_close_leader_screen"](stock).__code__)
    GAME = Game(turn=207); GAME.conn.view = "visible"; GAME.conn.blockers = False; GAME.conn.advance_on_poll = 208
    out = await wrapped(ctx=CTX)
    check("end_turn closes a screen left open first", GAME.conn.view == "hidden" and out.startswith("Turn 207 -> 208"),
          (GAME.conn.view, out[:40]))

    # 10. A hang reload is named: civ6-mcp reloads the turn's start and ends it again (game 8, turn 209).
    check("GameState.end_turn records results", GameState.end_turn is ns["_gs_end_turn_recorded"])
    tool = mcp._tool_manager.get_tool("end_turn")
    check("end_turn tool: hang note outside the units/pending wrapper", tool.fn.__code__ is bound
          and tool.fn.__wrapped__.__code__ is ns["_hang_note"](stock).__code__
          and tool.fn.__wrapped__.__wrapped__.__code__ is ns["_units_first"](stock).__code__)
    import inspect
    src_et = inspect.getsource(tool.fn.__wrapped__.__wrapped__.__wrapped__)
    check("civ6-mcp's end_turn tool calls gs.end_turn for the first try and the retry",
          "gs.end_turn)" in src_et and "result = await gs.end_turn()" in src_et)
    for script, want in (
            (["HANG:209:0_MCP_0209|End turn requested", "Cannot end turn \u2014 resolve these blockers: research"],
             "The result of ending it again is below"),
            (["HANG:207:0_MCP_0207|stuck", "Turn 207 -> 208 | Score: 435"], "The turn then ended without them"),
            (["HANG:13:0_MCP_0013|x", "HANG:13:0_MCP_0013|x", "Turn 13 -> 14"], "(2 times)")):
        steps = list(script)
        async def scripted(self): return steps.pop(0)
        ns["_original_gs_end_turn"] = scripted
        async def recovering(ctx=None):
            r = await GameState.end_turn(GAME)
            while r.startswith("HANG:"): r = await GameState.end_turn(GAME)
            return r
        out = await ns["_hang_note"](recovering)(ctx=CTX)
        turn = script[0].split(":")[1]
        check(f"hang note for turn {turn}", out.startswith(f"The AI turns hung after you ended turn {turn}")
              and want in out and out.endswith(script[-1]), repr(out[:200]))
    steps = ["Turn 5 -> 6"]
    out = await ns["_hang_note"](recovering)(ctx=CTX)
    check("no note without a hang", out == "Turn 5 -> 6", repr(out))

    # 11. Move-and-attack: civ6-mcp reads the unit's tile before the order runs and always says STOPPED_SHORT. The
    #     wrapper reads the unit and the target tile again until the order has played out.
    class AttackConn:
        def __init__(self, states): self.states, self.reads = list(states), 0
        async def execute_write(self, lua, timeout=None):
            assert "'ME|'" in lua and "Map.GetUnitsAt(43, 45)" in lua and "GetUnit(me, 9)" in lua, lua
            self.reads += 1
            return (self.states.pop(0) if len(self.states) > 1 else self.states[0]) + [lq.SENTINEL]
    class AttackGame:
        def __init__(self, states): self.conn = AttackConn(states)
    EST = "Combat Estimate (Melee):\n  Est damage to defender: ~44\n"
    async def stopped_short(self, ui, tx, ty):
        return (EST + "Error: STOPPED_SHORT|Unit moved to (42,43) but could not reach target at (43,45) — 2 tiles "
                "away. Movement exhausted by terrain. Try again next turn from closer position.")
    async def adjacent(self, ui, tx, ty): return EST + "MELEE_ATTACK|target:UNIT_WARRIOR at (43,45)|enemy HP:41 -> 41/100"
    attack = GameState.__dict__["attack_unit"]
    START = ["ME|42|43|2|100|4", "FOE|UNIT_WARRIOR|41|20"]
    cases = [
        ("kill and advance", [START, START, ["ME|43|45|0|88|0"]], 3,
         EST + "MELEE_ATTACK|target:UNIT_WARRIOR at (43,45)|moved from (42,43) and advanced into (43,45)|enemy HP:41 -> "
               "killed|your HP:100 -> 88|moves left: 0"),
        ("attack, target survives", [START, ["ME|43|44|1|78|0", "FOE|UNIT_WARRIOR|12|20"]], 2,
         EST + "MELEE_ATTACK|target:UNIT_WARRIOR at (43,45)|moved from (42,43) and attacked from (43,44)|enemy HP:41 -> "
               "12|your HP:100 -> 78|moves left: 0"),
        ("civilian captured", [["ME|42|43|2|100|4", "FOE|UNIT_BUILDER|100|0"], ["ME|43|45|0|100|0"]], 2,
         EST + "MELEE_ATTACK|target:UNIT_BUILDER at (43,45)|moved from (42,43) and advanced into (43,45)|enemy HP:100 -> "
               "captured|your HP:100 -> 100|moves left: 0"),
        ("unit died", [START, ["ME|GONE", "FOE|UNIT_WARRIOR|30|20"]], 2,
         EST + "MELEE_ATTACK|target:UNIT_WARRIOR at (43,45)|Your unit moved from (42,43) to attack and no longer exists: "
               "it died in the attack."),
        ("moved next to it, no attack", [START, ["ME|43|44|1|100|1", "FOE|UNIT_WARRIOR|41|20"]], 13,
         EST + "MOVED_ADJACENT|Unit moved from (42,43) to (43,44), next to UNIT_WARRIOR at (43,45), and did not attack "
               "(moves left: 1). It can attack again this turn."),
        ("really stopped short", [START, ["ME|44|44|2|100|0", "FOE|UNIT_WARRIOR|41|20"]], 13,
         EST + "Error: STOPPED_SHORT|Unit moved from (42,43) to (44,44) but could not reach UNIT_WARRIOR at (43,45): 2 "
               "tiles away, moves left: 0. No attack happened."),
        ("never moved", [START], 13,
         EST + "Error: NOT_MOVED|The move-and-attack order was sent, but after 6 seconds the unit is still at (42,43) "
               "and no combat has happened. Check get_units before you order it again."),
    ]
    ns["_original_attack_unit"] = stopped_short
    for name, states, reads, want in cases:
        g = AttackGame(states)
        out = await attack(g, 9, 43, 45)
        check(f"move-and-attack: {name}", out == want and g.conn.reads == reads, f"{g.conn.reads} reads: {out!r}")
    ns["_original_attack_unit"] = adjacent
    g = AttackGame([START])
    out = await attack(g, 9, 43, 45)
    check("adjacent attack passes through, one read", out == EST + "MELEE_ATTACK|target:UNIT_WARRIOR at (43,45)|enemy "
          "HP:41 -> 41/100" and g.conn.reads == 1, f"{g.conn.reads} reads: {out!r}")
    class Failing:
        async def execute_write(self, lua, timeout=None): raise TimeoutError
    ns["_original_attack_unit"] = stopped_short
    g = AttackGame([]); g.conn = Failing()
    out = await attack(g, 9, 43, 45)
    check("read failure keeps civ6-mcp's answer", "Try again next turn" in out, repr(out[-60:]))
    check("unit_action's attack calls the patched method", GameState.attack_unit is ns["_attack_unit_settled"])

    # 12. A ranged unit never falls back to a melee move; a refused adjacent shot is tried once more.
    lua = lq.build_attack_unit(9, 43, 45)
    check("ranged units take the ranged path", ns["_IS_RANGED"].rstrip("\n") + " or " + ns["_RANGED_UNIT"] in lua)
    check("no melee fallback for ranged units", f"elseif dist <= 1 and not {ns['_RANGED_UNIT']} then" in lua
          and 'print("ERR:RANGED_REFUSED|' in lua and "on (43,45) next to it" in lua
          and lua.index("ERR:RANGED_REFUSED") < lua.index("UnitOperationTypes.MOVE_TO"))
    check("the estimate counts an adjacent shot as ranged",
          "local isRanged = attRS > 0\n" in lq.build_combat_estimate_query(9, 43, 45))
    REFUSED = EST + "Error: RANGED_REFUSED|The game would not let UNIT_ARCHER fire from (39,40) at UNIT_WARRIOR on (43,45)"
    FIRED = EST + "RANGE_ATTACK|target:UNIT_WARRIOR at (43,45)|pre_hp:51/100|your HP:100|range:2 dist:1"
    for name, script, want in (("refused once, fires on the retry", [REFUSED, FIRED], FIRED),
                               ("refused twice: the error, unit not moved", [REFUSED, REFUSED], REFUSED),
                               ("fires at once: no retry", [FIRED, REFUSED], FIRED)):
        calls = []
        async def scripted(self, ui, tx, ty, script=script):
            calls.append(1)
            return script[len(calls) - 1]
        ns["_original_attack_unit"] = scripted
        out = await attack(AttackGame([START]), 9, 43, 45)
        check(f"ranged: {name}", out == want and len(calls) == (1 if name.startswith("fires") else 2), out[-60:])

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
check("civ6-mcp's bring-to-front calls the z-order raise",
      "_bring_to_front_win32()" in inspect.getsource(launcher._bring_to_front)
      and launcher._bring_to_front_win32 is ns["_bring_to_front_win32_raised"])
check("civ6-mcp's click starts away from the target",
      "_click_win32(x, y)" in inspect.getsource(launcher._click) and launcher._click_win32 is ns["_click_win32_moving"])
shutil.rmtree(TMP, ignore_errors=True)
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
