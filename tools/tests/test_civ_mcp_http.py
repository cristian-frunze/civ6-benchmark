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
    chain, f = [], tool.fn
    while f is not None:
        chain.append(f.__code__); f = getattr(f, "__wrapped__", None)
    want = [bound] + [ns[w](stock).__code__ for w in ("_names_promotions", "_explores_again", "_hang_note", "_units_first")]
    check("end_turn tool: promotions named, explore, hang note, then the units/pending wrapper", chain[:5] == want)
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

    # 13. Promotions follow the game's rule: heal EXPERIENCE_PROMOTE_HEALED HP (not to full), end the unit's turn.
    lua = lq.build_promote_unit(9, "PROMOTION_BATTLECRY")
    check("promotion: no full heal", "SetDamage(0)" not in lua)
    check("promotion: heals the game's amount", "GlobalParameters['EXPERIENCE_PROMOTE_HEALED']" in lua
          and "unit:SetDamage(math.max(0, unit:GetDamage() - healed))" in lua)
    check("promotion: ends the unit's turn", "UnitManager.FinishMoves(unit)" in lua
          and lua.index("exp:SetPromotion") < lua.index("FinishMoves"))
    check("promotion: the agent is told", "the unit's turn has ended (the game's rule for promotions)" in lua)

    # 15. City attack: the NO_LOS message names the tile instead of concatenating a Lua table.
    lua = lq.build_city_attack(393221, 46, 29)
    check("city attack NO_LOS message is plain text", "{target_x}" not in lua and "{target_y}" not in lua
          and 'Line of sight to (46,29) is blocked from (" .. cx' in lua)

    # 16. Units the agent used up are not reported as killed.
    from civ_mcp.lua.models import UnitInfo, TurnSnapshot
    def U(uid, name, ut, x, y, charges=0):
        return UnitInfo(unit_id=uid, unit_index=uid % 65536, name=name, unit_type=ut, x=x, y=y, moves_remaining=0,
                        max_moves=2, health=100, max_health=100, build_charges=charges)
    before = TurnSnapshot(turn=17, units={1: U(1, "Settler", "UNIT_SETTLER", 41, 41), 2: U(2, "Builder", "UNIT_BUILDER", 40, 40, 1),
                                          3: U(3, "Builder", "UNIT_BUILDER", 42, 42, 3), 4: U(4, "Warrior", "UNIT_WARRIOR", 43, 43),
                                          5: U(5, "Slinger", "UNIT_SLINGER", 44, 44)},
                          cities={}, current_research="", current_civic="")
    after = TurnSnapshot(turn=18, units={}, cities={}, current_research="", current_civic="")
    async def act(ctx=None, unit_id=None, action=None, **k):
        return "Error: NO_MOVES|x" if unit_id == 4 else "OK"
    rec = ns["_records_spent"](act)
    for uid, a in ((1, "found_city"), (2, "improve"), (3, "improve"), (4, "delete"), (6, "move")):
        await rec(ctx=CTX, unit_id=uid, action=a)
    async def upg(ctx=None, unit_id=None): return "UPGRADED|UNIT_ARCHER"
    await ns["_records_spent"](upg, action="upgrade")(ctx=CTX, unit_id=5)
    msgs = {e.message: e.priority for e in GameState._diff_snapshots(before, after)}
    check("settler that founded a city", msgs.get("Your Settler (UNIT_SETTLER) was used to found a city (last seen at (41,41)).") == 3, msgs)
    check("builder on its last charge", msgs.get("Your Builder (UNIT_BUILDER) used its last build charge (last seen at (40,40)).") == 3)
    check("builder with charges to spare is still 'killed'", msgs.get("Your Builder (UNIT_BUILDER) was killed! Last seen at (42,42).") == 1)
    check("failed order: still 'killed'", msgs.get("Your Warrior (UNIT_WARRIOR) was killed! Last seen at (43,43).") == 1)
    check("upgrade", msgs.get("Your Slinger (UNIT_SLINGER) was upgraded and has a new id (last seen at (44,44)).") == 3)
    check("cleared after the report", ns["_SPENT"] == {}, ns["_SPENT"])

    # 17. Unrevealed resources stay hidden in get_cities, get_builder_tasks and the wonder advisor.
    for name, lua in (("cities", lq.build_cities_query()), ("builder tasks", lq.build_builder_tasks_query()),
                      ("wonder advisor", lq.build_wonder_advisor_query(65536, "BUILDING_PYRAMIDS"))):
        body = lua.split("end\n", 1)[1]
        check(f"{name}: resources read through the reveal check", lua.startswith("local function __benchRes(plot)")
              and "__benchRes(plot)" in body and "plot:GetResourceType()" not in body)

    # 18. The promotion blocker names the units; the GP advisor finds the class in GreatPersonClasses.
    class PromoConn:
        async def execute_read(self, lua, timeout=None):
            assert "GetExperienceForNextLevel" in lua
            return ["PROMO|655366|UNIT_ARCHER|39,41", "PROMO|720898|UNIT_SUMERIAN_WAR_CART|43,38", lq.SENTINEL]
    class PromoGame:
        conn = PromoConn()
    GAME = PromoGame()
    blocked = "Cannot end turn:\n  * Unit available for promotion  -> Use: get_unit_promotions(unit_id=...) then promote_unit()"
    async def et_blocked(ctx=None): return blocked
    out = await ns["_names_promotions"](et_blocked)(ctx=CTX)
    check("promotion blocker names the units", "* Unit available for promotion (UNIT_ARCHER 655366 at (39,41); "
          "UNIT_SUMERIAN_WAR_CART 720898 at (43,38))  -> Use:" in out, out)
    async def et_plain(ctx=None): return "Turn 5 -> 6"
    check("no blocker: unchanged", await ns["_names_promotions"](et_plain)(ctx=CTX) == "Turn 5 -> 6")
    lua = lq.build_gp_advisor_query(9)
    check("GP advisor looks the class up in GreatPersonClasses", "for row in GameInfo.GreatPersonClasses() do" in lua
          and lua.index("GreatPersonClasses()") < lua.index('if gpClass == "" then'))

    # 19. A production order the game holds (open popup or diplomacy session) is not reported as a silent failure.
    from types import SimpleNamespace
    SILENT = ("Error: SILENT_FAILURE|BUILDING_WORKSHOP appeared to set but the game engine did not persist it "
              "(NOT_SET|current=NONE|expected=BUILDING_WORKSHOP). Retry the same call, or use purchase_item to "
              "force-commit with gold/faith.")
    class ProdConn:
        def __init__(self, lands_after): self.lands_after, self.reads = lands_after, 0
        async def execute_read(self, lua, timeout=None):
            assert 'cur == "BUILDING_WORKSHOP"' in lua and "FindID(65536 % 65536)" in lua, lua
            self.reads += 1
            if self.lands_after is not None and self.reads >= self.lands_after:
                return ["CONFIRMED|5 turns", lq.SENTINEL]
            return ["NOT_SET|current=NONE|expected=BUILDING_WORKSHOP", lq.SENTINEL]
    class ProdGame:
        def __init__(self, lands_after=None, sessions=(), popups="No popups to dismiss."):
            self.conn, self.sessions, self.popups, self.dismissed = ProdConn(lands_after), list(sessions), popups, 0
        async def get_diplomacy_sessions(self): return self.sessions
        async def dismiss_popup(self):
            self.dismissed += 1
            return self.popups
    setprod = GameState.__dict__["set_city_production"]
    check("set_city_production is the patched method", setprod is ns["_set_production_settled"])
    germany = SimpleNamespace(other_civ_name="Germany", other_leader_name="Frederick Barbarossa")
    cases = [
        ("confirmed at once: passed through", ProdGame(), ["PRODUCING|BUILDING_WORKSHOP|5 turns"],
         "PRODUCING|BUILDING_WORKSHOP|5 turns", 1, 0),
        ("diplomacy session open: named, nothing closed or resent", ProdGame(sessions=[germany]), [SILENT],
         "Error: ORDER_HELD|BUILDING_WORKSHOP is not set yet: a diplomacy session with Germany (Frederick Barbarossa) "
         "is open, and the game holds city orders until you answer it (get_pending_diplomacy, then "
         "respond_to_diplomacy or respond_to_trade). The order then goes through by itself; check the city before "
         "you set it again.", 1, 0),
        ("popups closed, order lands", ProdGame(lands_after=2, popups="Dismissed: cinematic_camera, NaturalWonderPopup, "
         "NaturalWonderPopup, InvitePopup, InvitePopup. Also: diplomacy session active — use respond_to_diplomacy."),
         [SILENT], "PRODUCING|BUILDING_WORKSHOP|5 turns (the game applied the order after open popups were closed "
         "(cinematic_camera, NaturalWonderPopup, InvitePopup))", 1, 1),
        ("no popups, order lands late", ProdGame(lands_after=1), [SILENT],
         "PRODUCING|BUILDING_WORKSHOP|5 turns (the game applied the order 0.5 s late)", 1, 1),
        ("never lands: sent once more", ProdGame(), [SILENT, "PRODUCING|BUILDING_WORKSHOP|5 turns"],
         "PRODUCING|BUILDING_WORKSHOP|5 turns", 2, 1),
    ]
    for name, g, script, want, sends, dismissed in cases:
        calls = []
        async def scripted(self, cid, it, nm, tx=None, ty=None, script=script):
            calls.append((cid, it, nm, tx, ty))
            return script[len(calls) - 1]
        ns["_original_set_production"] = scripted
        out = await setprod(g, 65536, "BUILDING", "BUILDING_WORKSHOP")
        check(f"production: {name}", out == want and len(calls) == sends and g.dismissed == dismissed,
              (len(calls), g.dismissed, out))

    # 22. Obsolete policies: not listed, and set_policies refuses them, naming the replacement.
    lua = lq.build_policies_query()
    check("get_policies skips obsolete policies", "pCulture:IsPolicyObsolete(policy.Hash)" in lua
          and "if pCulture:IsPolicyUnlocked(policy.Index) and not (obsOk and isObs) then" in lua)
    orig = ns["_original_set_policies"]({0: "POLICY_CONSCRIPTION", 4: "NONE"})
    lua = lq.build_set_policies({0: "POLICY_CONSCRIPTION", 4: "NONE"})
    check("set_policies checks obsolescence before CanSlotPolicy", "IsPolicyObsolete(pe_0.Hash)" in lua
          and lua.index("IsPolicyObsolete(pe_0.Hash)") < lua.index("local canSlot_0 = ")
          and "ERR:POLICY_OBSOLETE|POLICY_CONSCRIPTION is obsolete" in lua and "replaced it" in lua
          and "GameInfo.ObsoletePolicies()" in lua)
    check("a cleared slot gets no check", "pe_4" not in lua and "obsOk_4" not in lua)
    i, j = lua.index("local obsOk_0"), lua.index("local canSlot_0 = ")
    check("nothing else in set_policies changes", lua[:i] + lua[j:] == orig)

    # 23. skip_remaining_units leaves units with orders of their own alone, after the game finishes moving units.
    check("skip_remaining_units is the patched method", GameState.skip_remaining_units is ns["_skip_remaining_ready"])
    class SkipConn:
        def __init__(self, keep_replies): self.keep_replies, self.writes, self.reads = list(keep_replies), [], []
        async def execute_write(self, lua, timeout=None):
            if "IsReadyToSelect" in lua:
                return self.keep_replies.pop(0) + [lq.SENTINEL]
            self.writes.append(lua)
            return ["OK:FORTIFIED|1 fortified, 0 healing", lq.SENTINEL]
        async def execute_read(self, lua, timeout=None):
            self.reads.append(lua)
            return ["OK:SKIPPED|3 units", lq.SENTINEL]
    class SkipGame:
        def __init__(self, replies): self.conn = SkipConn(replies)
    g = SkipGame([["BUSY|true"], ["BUSY|false", "KEEP|196608", "KEEP|262146"]])
    out = await GameState.__dict__["skip_remaining_units"](g)
    spared = "unit:GetMovesRemaining() > 0 and not __keep[unit:GetID()] then"
    check("skip waits for the game, then spares the units with orders",
          g.conn.keep_replies == [] and len(g.conn.writes) == 1 and len(g.conn.reads) == 1
          and g.conn.writes[0].startswith("local __keep = {[196608] = true, [262146] = true}\n")
          and spared in g.conn.writes[0] and g.conn.reads[0].startswith("local __keep = {[196608] = true")
          and spared in g.conn.reads[0] and "UnitManager.FinishMoves(unit)" in g.conn.reads[0], g.conn.writes[:1])
    check("skip reports what it left alone", out == "FORTIFIED|1 fortified, 0 healing\nSKIPPED|3 units\nKEPT|2 units the "
          "game does not count as waiting for orders (on auto-explore, still moving, fortified or asleep) were left "
          "alone", out)
    g = SkipGame([["BUSY|false"]])
    out = await GameState.__dict__["skip_remaining_units"](g)
    check("no units with orders: civ6-mcp's Lua unchanged", g.conn.writes == [lq.build_fortify_remaining_units()]
          and g.conn.reads == [lq.build_skip_remaining_units()] and out == "FORTIFIED|1 fortified, 0 healing\nSKIPPED|3 units", out)

    # 24. A move that reaches its tile with no moves left says so; so does a refused activation.
    check("move_unit and activate_great_person are patched", GameState.move_unit is ns["_move_says_moves_left"]
          and GameState.activate_great_person is ns["_activate_says_no_moves"])
    class MovesConn:
        def __init__(self, moves): self.moves, self.reads = moves, []
        async def execute_read(self, lua, timeout=None):
            self.reads.append(lua)
            return ([f"MOVES|{self.moves}"] if self.moves is not None else []) + [lq.SENTINEL]
    def moves_game(moves): return SimpleNamespace(conn=MovesConn(moves))
    arrived = "MOVING_TO|44,40|from:44,41|now_at:44,40|(moved dx:+0 dy:-1)\nRevealed 3 tiles"
    for name, result, moves, want in (
        ("arrived, 0 moves: said on the first line", arrived, 0,
         "MOVING_TO|44,40|from:44,41|now_at:44,40|(moved dx:+0 dy:-1)|arrived with no moves left: it can build, "
         "found or activate there next turn\nRevealed 3 tiles"),
        ("arrived with moves: unchanged", arrived, 1, arrived),
        ("stopped mid path: unchanged", "MOVING_TO|40,42|from:42,39|now_at:42,40|STOPPED_MID_PATH (moves exhausted)", 0,
         "MOVING_TO|40,42|from:42,39|now_at:42,40|STOPPED_MID_PATH (moves exhausted)"),
        ("blocked: unchanged", "MOVING_TO|44,40|from:44,40|now_at:44,40|BLOCKED (x)", 0,
         "MOVING_TO|44,40|from:44,40|now_at:44,40|BLOCKED (x)"),
        ("unit gone: unchanged", arrived, None, arrived),
        ("error: unchanged", "Error: UNIT_NOT_FOUND", 0, "Error: UNIT_NOT_FOUND")):
        async def fake_move(self, i, x, y, _r=result): return _r
        ns["_original_move_unit"] = fake_move
        out = await GameState.move_unit(moves_game(moves), 1, 44, 40)
        check(f"move: {name}", out == want, out)
    near = "MOVING_TO|4,40|from:5,41|now_at:4,40|(moved dx:-1 dy:-1)"
    async def fake_move(self, i, x, y): return near
    ns["_original_move_unit"] = fake_move
    check("move: a target that is a prefix of now_at is not an arrival",
          await GameState.move_unit(moves_game(0), 1, 4, 4) == near)
    refused = "Error: CANNOT_ACTIVATE|Isaac Newton (UNIT_GREAT_SCIENTIST) at (42,40) charges=1. Valid tiles: 42,40=DISTRICT_CAMPUS"
    for moves, want in ((0, refused + " It has no moves left this turn, and a great person needs moves to activate: "
                         "activate it on the same tile next turn."), (2, refused)):
        async def fake_act(self, i): return refused
        ns["_original_activate"] = fake_act
        out = await GameState.activate_great_person(moves_game(moves), 1)
        check(f"activate refused with {moves} moves", out == want, out)
    async def fake_act(self, i): return "GP_ACTIVATED|Isaac Newton at 42,40"
    ns["_original_activate"] = fake_act
    g = moves_game(0)
    check("activate that worked: unchanged, no query", await GameState.activate_great_person(g, 1)
          == "GP_ACTIVATED|Isaac Newton at 42,40" and g.conn.reads == [])

    # 25. A turn that ends after civ6-mcp closes a session from a civ at war: the report names the new turn and the
    #     advisor budget resets (game 9, turn 144: "Turn 144 -> 144"); the autosave is named for the turn it holds.
    check("execute_end_turn and the end-turn autosave are patched",
          et.execute_end_turn is ns["_end_turn_reports_turn_on"] and et.save_game is ns["_autosave_of_turn_on"])
    class WarConn(Conn):
        async def execute_write(self, lua, timeout=None):
            if '"EXIT" == "EXIT"' in lua: self.turn = 145  # the AI turns finish once the session is closed
            return await super().execute_write(lua, timeout)
    class WarGame(Game):
        def __init__(self):
            super().__init__(turn=144)
            self.conn = WarConn(144); self.conn.blockers = False
            self._high_water_turn, self._advisor_calls_this_turn = 144, 7
        async def get_diplomacy_sessions(self):
            return [] if self.conn.turn > 144 or not self.conn.endturn_sent else [SimpleNamespace(
                is_at_war=True, other_player_id=4, other_civ_name="Brazil", other_leader_name="Pedro II",
                dialogue_text="War!", reason_text="", deal_summary="", buttons="")]
    GAME = WarGame()
    unfixed = await ns["_original_execute_end_turn"](GAME)
    check("war session, unfixed: civ6-mcp reports the old turn", unfixed.startswith("Turn 144 -> 144"),
          repr(unfixed[:40]))
    check("war session, unfixed: advisor budget not reset", GAME._advisor_calls_this_turn == 7)
    GAME = WarGame()
    out = await stock()
    check("war session: the report names the new turn", out.startswith("Turn 144 -> 145"), repr(out[:40]))
    check("war session: only the turn number changed", out == unfixed.replace("Turn 144 -> 144", "Turn 144 -> 145", 1))
    check("war session: advisor budget reset, high-water turn 145",
          GAME._advisor_calls_this_turn == 0 and GAME._high_water_turn == 145)
    check("war session: one end-turn request", GAME.conn.endturn_sent == 1, GAME.conn.endturn_sent)
    real_execute = ns["_original_execute_end_turn"]
    try:
        for name, report, turn, want in (
            ("same turn while the game is still on it: unchanged", "Turn 50 -> 50 | Score: 9\nx", 50,
             "Turn 50 -> 50 | Score: 9\nx"),
            ("an advancing report: unchanged", "Turn 50 -> 51 | Score: 9", 52, "Turn 50 -> 51 | Score: 9"),
            ("game over after the war session", "Turn 50 -> 50\nGAME OVER — VICTORY!", 51,
             "Turn 50 -> 51\nGAME OVER — VICTORY!"),
            ("not a report: unchanged", "Cannot end turn: a unit still needs orders", 51,
             "Cannot end turn: a unit still needs orders")):
            async def fake_execute(gs, _r=report): return _r
            ns["_original_execute_end_turn"] = fake_execute
            GAME = Game(turn=turn)
            out = await stock()
            check(f"report: {name}", out == want, repr(out))
    finally:
        ns["_original_execute_end_turn"] = real_execute
    real_autosave = ns["_original_autosave"]
    try:
        saved = []
        async def fake_save(conn, name): saved.append(name); return "saved"
        ns["_original_autosave"] = fake_save
        for name, given, turn, want in (
            ("named for the turn the game is on", "0_MCP_0144", 145, "0_MCP_0145"),
            ("right name: unchanged", "0_MCP_0145", 145, "0_MCP_0145"),
            ("other saves: unchanged", "BENCH_PANGAEA_ONLINE_T1", 145, "BENCH_PANGAEA_ONLINE_T1")):
            saved.clear()
            await et.save_game(Conn(turn), given)
            check(f"autosave: {name}", saved == [want], saved)
        class NoTurn(Conn):
            async def execute_read(self, lua, timeout=None): raise RuntimeError("no answer")
        saved.clear()
        await et.save_game(NoTurn(145), "0_MCP_0144")
        check("autosave: turn unreadable, name kept", saved == ["0_MCP_0144"], saved)
    finally:
        ns["_original_autosave"] = real_autosave

    # 26. The turn snapshot's units read goes to InGame, as get_units does: GameCore has no
    #     UnitManager.CanStartOperation, so civ6-mcp's line-of-sight check failed the whole read (309 times).
    import inspect
    from civ_mcp.connection import GameConnection
    check("execute_read is patched", GameConnection.execute_read is ns["_units_read_in_game"])
    check("the snapshot still reads the units with the same query in GameCore",
          "execute_read(lq.build_units_query())" in inspect.getsource(GameState._take_snapshot)
          and lq.build_units_query() == lq.build_units_query() and "CanStartOperation" in lq.build_units_query())
    class StateConn:
        def __init__(self): self.calls = []
        async def execute_write(self, lua, timeout=5.0): self.calls.append(("InGame", lua)); return ["w"]
    real_read = ns["_original_execute_read"]
    try:
        async def fake_read(self, lua, timeout=5.0): self.calls.append(("GameCore", lua)); return ["r"]
        ns["_original_execute_read"] = fake_read
        c = StateConn()
        out = await GameConnection.execute_read(c, lq.build_units_query())
        check("units query: sent to InGame", c.calls == [("InGame", lq.build_units_query())] and out == ["w"])
        c = StateConn()
        out = await GameConnection.execute_read(c, "print(Game.GetCurrentGameTurn())", timeout=3.0)
        check("other reads: still GameCore", c.calls == [("GameCore", "print(Game.GetCurrentGameTurn())")]
              and out == ["r"])
    finally:
        ns["_original_execute_read"] = real_read

    # 28. The HTTP server keeps idle connections an hour, not uvicorn's 5 s (ECONNRESET 4.1 to 5.0 s after a result).
    import uvicorn
    check("keep-alive raised", uvicorn.Config(app=None).timeout_keep_alive == 3600
          and uvicorn.Config(app=None, timeout_keep_alive=7).timeout_keep_alive == 7)

    # 27. Base-game spy missions civ6-mcp leaves out: DISRUPT_ROCKETRY (game 11 answered UNKNOWN_MISSION) and
    #     LISTENING_POST. The hash rule reproduces every hash civ6-mcp hardcodes.
    import civ_mcp.lua.espionage as esp
    bc = ns["bc"]
    names = {"TRAVEL": "TRAVEL_NEW_CITY"}
    check("op hash rule matches civ6-mcp's table",
          all(bc.op_hash("UNITOPERATION_SPY_" + names.get(k, k)) == v
              for k, v in esp._SPY_OP_HASHES.items() if k not in bc.SPY_OPS))
    check("DISRUPT_ROCKETRY and LISTENING_POST added",
          esp._SPY_OP_HASHES.get("DISRUPT_ROCKETRY") == -1021949976
          and esp._SPY_OP_HASHES.get("LISTENING_POST") == -955496600)
    lua = lq.build_spy_mission(7, "disrupt_rocketry", 54, 16)
    check("spy_action builds the mission", "UNKNOWN_MISSION" not in lua and "-1021949976" in lua
          and "RequestOperation(unit, -1021949976" in lua, lua[:200])
    check("get_spies checks it", "DISRUPT_ROCKETRY=-1021949976" in lq.build_get_spies_query())
    check("spy_action's description names it", "DISRUPT_ROCKETRY, against a city with a Spaceport"
          in mcp._tool_manager.get_tool("spy_action").description)
    # 29. The mission lists name the base game's missions (game 13: get_spies still listed NEUTRALIZE_GOVERNOR and
    #     FABRICATE_SCANDAL, which the base game lacks, and not DISRUPT_ROCKETRY).
    import civ_mcp.narrate as nar
    from civ_mcp.lua.models import SpyInfo
    spies_out = nar.narrate_spies([SpyInfo(unit_id=7, unit_index=7, name="Farrah", x=54, y=16, rank=1, xp=0, moves=1,
                                           city_name="Argos", city_owner=3, available_ops=["DISRUPT_ROCKETRY"])])
    rules_out = spies_out
    for rx, rep in bc.OUTPUT_RULES["get_spies"]:
        rules_out = rx.sub(rep, rules_out)
    check("get_spies mission list rewritten", "FABRICATE_SCANDAL" in spies_out and "FABRICATE_SCANDAL" not in rules_out
          and "DISRUPT_ROCKETRY, LISTENING_POST" in rules_out, rules_out[-400:])
    desc = mcp._tool_manager.get_tool("spy_action").description
    check("spy_action mission list rewritten", "NEUTRALIZE_GOVERNOR" not in desc
          and "RECRUIT_PARTISANS, DISRUPT_ROCKETRY, LISTENING_POST" in desc, desc[:600])

    # 21. The popup scan skips InvitePopup, which never hides, and puts it back afterwards.
    import civ_mcp.game_lifecycle as glc
    check("dismiss_popup is the patched function", glc.dismiss_popup is ns["_dismiss_skipping"])
    seen_states = []
    async def fake_dismiss(conn):
        seen_states.append(dict(conn.lua_states))
        return "Dismissed: NaturalWonderPopup"
    ns["_original_dismiss"] = fake_dismiss
    conn = SimpleNamespace(lua_states={1: "InGame", 57: "InvitePopup", 60: "NaturalWonderPopup"})
    out = await glc.dismiss_popup(conn)
    check("InvitePopup left out of the scan and restored", seen_states == [{1: "InGame", 60: "NaturalWonderPopup"}]
          and conn.lua_states == {1: "InGame", 57: "InvitePopup", 60: "NaturalWonderPopup"}
          and out == "Dismissed: NaturalWonderPopup", (seen_states, conn.lua_states))

    # 20. Diplomacy pauses carry the player id; NO_SESSION names the sessions that are open.
    spain = SimpleNamespace(other_civ_name="Spain", other_leader_name="Philip II", other_player_id=7)
    class DiploGame:
        def __init__(self, sessions): self.sessions = sessions
        async def get_diplomacy_sessions(self): return self.sessions
    paused = ('Turn paused — AI diplomatic proposal from Spain (Philip II) [active].\nSpain (Philip II) says: "Hola"\n'
              "Use respond_to_diplomacy to handle it, then end_turn again.")
    out = await ns["_with_player_ids"](DiploGame([spain]), paused)
    check("pause names the player id, only on the pause line",
          out.startswith("Turn paused — AI diplomatic proposal from Spain (Philip II, player 7) [active].")
          and '\nSpain (Philip II) says: "Hola"' in out, out)
    pending = "Cannot end turn: diplomacy encounter pending with Spain (Philip II) [active]. Use respond_to_diplomacy."
    check("blocker names the player id", "pending with Spain (Philip II, player 7) [active]"
          in await ns["_with_player_ids"](DiploGame([spain]), pending))
    check("no pause: unchanged, no query", await ns["_with_player_ids"](None, "Turn 5 -> 6") == "Turn 5 -> 6")
    check("respond_to_diplomacy calls the patched method", GameState.diplomacy_respond is ns["_respond_names_sessions"])
    for name, script, sessions, want in (
        ("wrong id: the open session is named", "Error: NO_SESSION", [spain],
         "Error: NO_SESSION|No diplomacy session is open with player 1. Open now: Spain (Philip II), player 7. Answer it "
         "with that player id."),
        ("nothing open", "Error: NO_SESSION", [],
         "Error: NO_SESSION|No diplomacy session is open with player 1. None is open now, so nothing is waiting for an "
         "answer."),
        ("answered: passed through", "OK:RESPONDED|POSITIVE|SESSION_CONTINUES", [spain],
         "OK:RESPONDED|POSITIVE|SESSION_CONTINUES")):
        async def respond(self, pid, resp, script=script): return script
        ns["_original_diplomacy_respond"] = respond
        out = await GameState.__dict__["diplomacy_respond"](DiploGame(sessions), 1, "POSITIVE")
        check(f"respond: {name}", out == want, out)

    # 14. Auto-explore: the harness remembers automated units and sends auto-explore again at each new turn.
    class ExploreConn:
        def __init__(self, units, active=True): self.units, self.active, self.sent = units, active, []
        async def execute_read(self, lua, timeout=None):
            return [f"ACTIVE|{str(self.active).lower()}", lq.SENTINEL]
        async def execute_write(self, lua, timeout=None):
            assert "UNITOPERATION_AUTOMATE_EXPLORE" in lua and "ipairs({" in lua, lua
            out = []
            for uid, st in sorted(self.units.items()):
                if st == "gone": out.append(f"EXPLORER|{uid}|GONE"); continue
                x, y, m, ok = st
                kind = "SENT" if m > 0 and ok else ("REFUSED" if m > 0 else "KEPT")
                if kind == "SENT": self.sent.append(uid)
                out.append(f"EXPLORER|{uid}|{kind}|{x}|{y}|{m}")
            return out + [lq.SENTINEL]
    class ExploreGame:
        def __init__(self, units, active=True): self.conn = ExploreConn(units, active)
    GAME = ExploreGame({})
    async def unit_action(ctx=None, unit_id=None, action=None, **k):
        return {"automate": "AUTOMATED|39,40", "move": "MOVING_TO|40,41"}[action]
    track = ns["_tracks_explorers"](unit_action)
    await track(ctx=CTX, unit_id=196608, action="automate")
    await track(CTX, unit_id=262146, action="automate")
    check("automate is remembered with its tile", GAME._bench_explorers == {196608: (39, 40), 262146: (39, 40)},
          GAME._bench_explorers)
    await track(ctx=CTX, unit_id=262146, action="move", target_x=40, target_y=41)
    check("another order ends it", GAME._bench_explorers == {196608: (39, 40)}, GAME._bench_explorers)
    script = ["Turn 6 -> 7 | Score: 10"]
    async def end_turn_fake(ctx=None): return script[0]
    et_wrapped = ns["_explores_again"](end_turn_fake)
    GAME.conn.units = {196608: (41, 42, 3, True)}
    out = await et_wrapped(ctx=CTX)
    check("explore sent again at the new turn", GAME.conn.sent == [196608] and out.startswith("Turn 6 -> 7")
          and "Auto-explore continues for unit 196608 from (41,42)" in out and GAME._bench_explorers[196608] == (41, 42),
          out)
    GAME.conn.units = {196608: (41, 42, 3, True)}; GAME.conn.sent = []
    out = await et_wrapped(ctx=CTX)
    check("unit that did not move: stopped and the agent told", GAME.conn.sent == [196608]
          and "Auto-explore has stopped for unit 196608 at (41,42)" in out and "continues" not in out
          and GAME._bench_explorers == {}, out)
    GAME._bench_explorers = {196608: (41, 42)}; GAME.conn.sent = []
    script[0] = "The AI turns hung after you ended turn 7, so the game was reloaded ...\n\nTurn 7 -> 8 | Score: 10"
    out = await et_wrapped(ctx=CTX)
    check("after a hang reload the same tile is not a stop", "continues for unit 196608" in out
          and 196608 in GAME._bench_explorers, out[-120:])
    GAME._bench_explorers = {196608: (41, 42), 5: (1, 1), 6: (2, 2)}
    GAME.conn.units = {196608: (43, 44, 0, True), 5: "gone", 6: (2, 3, 3, False)}; GAME.conn.sent = []
    script[0] = "Turn 8 -> 9 | Score: 11"
    out = await et_wrapped(ctx=CTX)
    check("no moves: kept quietly; gone: dropped; refused: stopped", GAME.conn.sent == []
          and GAME._bench_explorers == {196608: (43, 44)} and "stopped for unit 6 at (2,3)" in out
          and "continues" not in out, (GAME._bench_explorers, out))
    script[0] = "Turn paused - AI diplomatic proposal from Brazil"
    out = await et_wrapped(ctx=CTX)
    check("no new turn: nothing sent", out == script[0] and GAME.conn.sent == [])
    GAME.conn.active = False; script[0] = "Turn 9 -> 10"; GAME.conn.units = {196608: (45, 44, 3, True)}
    out = await et_wrapped(ctx=CTX)
    check("AI civs still moving: nothing sent", out == "Turn 9 -> 10" and GAME.conn.sent == [])
    tools = mcp._tool_manager
    chain, f = [], tools.get_tool("unit_action").fn
    while f is not None:
        chain.append(f.__code__); f = getattr(f, "__wrapped__", None)
    check("unit_action carries the explorer tracking", ns["_tracks_explorers"](stock).__code__ in chain)

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
