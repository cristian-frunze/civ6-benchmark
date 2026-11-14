"""Offline tests of windows/civ_mcp_http.py's fixes to civ6-mcp: the diplomacy-pause fix and the dropped end-turn
request, run against civ6-mcp's real execute_end_turn with a fake game connection; the diplomacy screen left locked
by trades; the note after a hang reload; the move-and-attack result; and the menu-load click retry. No game or
network needed.

    cd vendor/civ6-mcp && uv run --frozen python ../../tools/tests/test_civ_mcp_http.py
"""
import asyncio, inspect as _inspect, logging, os, shutil, sys, tempfile, types
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
        if any(k in lua for k in ("BENCH_DEALS", "CLOSED|", "TERMS|", "DEAL_REJECTED", "PROPOSED_ITEMS", "CLEARED")):
            return self.deal(lua)
        return [lq.SENTINEL]
    # The trade protocol: the AI answers a proposal or a test in a later statement event, and a deal it accepts
    # is enacted after the player's ACCEPTED (an E event).
    deal_answer, deal_enacts, deal_leftover = "ACCEPTED", True, None  # leftover: None, "session" or "hidden"
    test_answer, deal_equal = "ADJUSTED", False  # deal_equal: an ADJUSTED answer kept our terms
    test_equal, inspect_answer = False, "ACCEPTED"  # test_equal: a test's answer gave our terms back unchanged
    def deal(self, lua):
        import re as _re
        self.deal_log = getattr(self, "deal_log", [])
        self.deal_ev = getattr(self, "deal_ev", [])
        if "for i = " in lua and "EV|" in lua:  # poll
            self.deal_log.append("poll")
            mark = int(_re.search(r"for i = (\d+) \+ 1", lua).group(1))
            evs = [f"EV|{e}" for i, e in enumerate(self.deal_ev, 1) if i > mark]
            closed = "close" in self.deal_log
            st = {None: "nil|false|false|0", "session": "3|false|true|2", "hidden": "nil|false|true|0"}
            state = st[self.deal_leftover] if closed else "3|false|false|0"
            return evs + [f"STATE|{state}", lq.SENTINEL]
        if "DealProposalAction.PROPOSED" in lua:  # live: an AI that accepts enacts the deal with its answer
            self.deal_log.append("propose")
            mark = len(self.deal_ev)
            if self.deal_answer: self.deal_ev.append(f"S|7|0|{self.deal_answer}|PROPOSED")
            if self.deal_answer == "ACCEPTED" and self.deal_enacts: self.deal_ev.append("E|7|0")
            return ["CIV|Spain", "TERMS|we give Coal (30 turns); they give 100 gold", f"MARK|{mark}", lq.SENTINEL]
        if "DealProposalAction.INSPECT" in lua:  # the deal view's check: ACCEPTED or REJECTED, nothing enacted
            self.deal_log.append("inspect")
            mark = len(self.deal_ev)
            if self.inspect_answer: self.deal_ev.append(f"S|7|0|{self.inspect_answer}|INSPECT")
            return ["CIV|7|Spain", f"MARK|{mark}", lq.SENTINEL]
        if "DealProposalAction.EQUALIZE" in lua:  # the game: its counter is read before the AI answers (stale)
            self.deal_log.append("test")
            mark = len(self.deal_ev)
            if self.test_answer: self.deal_ev.append(f"S|7|0|{self.test_answer}|EQUALIZE")
            return ["CIV|7|Spain", "PROPOSED_ITEMS", "ITEM|US|RESOURCE|1|30|5|", f"MARK|{mark}", "AI_COUNTER",
                    "ITEM|THEM|GOLD|93|0||", lq.SENTINEL]
        if "PROPOSED_ITEMS" in lua:  # read again after the answer
            self.deal_log.append("reread")
            return ["CIV|7|Spain", "PROPOSED_ITEMS", "ITEM|US|RESOURCE|1|30|5|", "AI_COUNTER",
                    "ITEM|US|RESOURCE|1|30|5|" if self.test_equal else "ITEM|THEM|GOLD|100|0||", lq.SENTINEL]
        if "DealProposalAction.ACCEPTED" in lua and "TERMS|" in lua:
            if "AreWorkingDealsEqual" in lua and not self.deal_equal:
                self.deal_log.append("accept-check")
                return ["NOT_EQUAL|we give Coal (30 turns); they give 40 gold", lq.SENTINEL]
            self.deal_log.append("accept-copy")
            mark = len(self.deal_ev)
            if self.deal_enacts: self.deal_ev.append("E|7|0")
            return ["TERMS|we give Coal (30 turns); they give 100 gold", f"MARK|{mark}", lq.SENTINEL]
        if "TERMS|" in lua:
            self.deal_log.append("incoming"); return ["TERMS|we give Coal (30 turns); they give 40 gold", lq.SENTINEL]
        if "CLEARED" in lua:
            self.deal_log.append("clear"); return ["CLEARED", lq.SENTINEL]
        if "CLOSED|" in lua:
            self.deal_log.append("close"); return [lq.SENTINEL]
        if "DEAL_REJECTED" in lua:
            self.deal_log.append("reject")
            if self.deal_leftover == "session": self.deal_leftover = None
            return ["OK:DEAL_REJECTED|Spain", lq.SENTINEL]
        return [lq.SENTINEL]

from civ_mcp.game_state import GameState
class Game:
    _build_turn_report = GameState.__dict__["_build_turn_report"]
    propose_trade = GameState.__dict__["propose_trade"]  # the wrapper's versions
    test_trade = GameState.__dict__["test_trade"]
    respond_to_deal = GameState.__dict__["respond_to_deal"]
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
    check("attack chain: settled, then the district attack, then civ6-mcp's",
          GameState.attack_unit is ns["_attack_unit_settled"] and ns["_original_attack_unit"] is ns["_attack_unit_districts"])

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
    check("GameState.propose_trade replaced", GameState.propose_trade is ns["_propose_trade_waits"])
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

    # 30. Trades wait for the AI's answer (game 12's turn-96 hang, replayed live: a test closed before the AI
    #     answered left Rome holding a deal it could never deliver, and its turn waited on it forever).
    ns["_deal_wait"].__defaults__ = (0.6,)  # the no-answer case waits this long instead of 6 s
    def trade(**conn_attrs):
        g = Game(turn=96)
        for k, v in conn_attrs.items(): setattr(g.conn, k, v)
        return g
    GAME = trade()
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    log = GAME.conn.deal_log
    check("accepted: reports the enacted deal", out.startswith("ACCEPTED|Spain accepted, and the deal is in effect: we give Coal"), out)
    check("accepted: no ACCEPTED of ours (it would enact the deal again)", not any(x.startswith("accept") for x in log), log)
    check("accepted: session closed after the answer", log.index("close", log.index("propose")) > log.index("propose") + 1, log)
    GAME = trade(deal_answer="ADJUSTED")
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("counter-offer: not accepted, terms shown", out.startswith("COUNTER|Spain did not accept") and "they give 40 gold" in out
          and "accept-copy" not in GAME.conn.deal_log, (out, GAME.conn.deal_log))
    GAME = trade(deal_answer="ADJUSTED", deal_equal=True)
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("ADJUSTED to the same terms: accepted once", out.startswith("ACCEPTED|Spain accepted")
          and GAME.conn.deal_log.count("accept-copy") == 1, (out, GAME.conn.deal_log))
    GAME = trade(deal_answer="REJECTED")
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("rejected", out.startswith("REJECTED|Spain rejected") and "accept-copy" not in GAME.conn.deal_log, out)
    GAME = trade(deal_answer=None)
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("no answer: nothing accepted", out.startswith("NO_ANSWER|") and "accept-copy" not in GAME.conn.deal_log, out)
    GAME = trade(deal_enacts=False)
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("accepted but not enacted: says so", out.startswith("UNCLEAR|"), out)
    GAME = trade(deal_leftover="session")
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("an offer the AI opens afterwards is refused", "reject" in GAME.conn.deal_log and "Warning" not in out,
          (GAME.conn.deal_log, out))
    GAME = trade(deal_leftover="hidden")
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("a deal that cannot be answered is named", "Warning: this civ still holds a deal" in out, out)
    GAME = trade(); GAME.conn.deal_leftover = "session"; GAME.conn.deal_log = ["close"]  # an AI offer is waiting
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("an AI offer waiting: answer it first", out.startswith("Error: OFFER_PENDING") and "propose" not in GAME.conn.deal_log, out)
    # The test: civ6-mcp's own Lua and report, without its immediate close; the session closes after the answer.
    lua = ns["bc"].mark_test_trade(lq.build_test_trade(7, [{"type": "RESOURCE", "name": "RESOURCE_COAL", "amount": 1, "duration": 30}], []))
    check("test Lua: marks before EQUALIZE, no close of its own", lua.index("MARK|") < lua.index("DealProposalAction.EQUALIZE")
          and "CloseSession" not in lua[lua.index("DealProposalAction.EQUALIZE"):], lua[-300:])
    GAME = trade()
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100, mode="test")
    log = GAME.conn.deal_log
    check("test: the counter-offer read after the answer", "AI counter-offer" in out and "100" in out
          and "93" not in out and log[:3] == ["test", "poll", "reread"], (out, log))
    check("test: closed after the AI answered", log.index("close") > log.index("reread"), log)
    check("test with a counter-offer: no INSPECT check", "inspect" not in log, log)
    rr = ns["bc"].reread_test_trade(lq.build_test_trade(7, [{"type": "RESOURCE", "name": "RESOURCE_COAL", "amount": 1, "duration": 30}], []))
    check("test re-read Lua sends and closes nothing", "SendWorkingDeal" not in rr and "CloseSession" not in rr
          and "RequestSession" not in rr and "AI_COUNTER" in rr and rr.rstrip().endswith(f'print("{lq.SENTINEL}")'), rr[-200:])
    for ans, want in (("REJECTED", "REJECTED"), (None, "NO ANSWER")):
        GAME = trade(test_answer=ans)
        out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100, mode="test")
        check(f"test answered {ans}: {want}, no stale counter", f"AI response: {want}" in out and "93" not in out
              and "reread" not in GAME.conn.deal_log, out)
    # Our terms back unchanged say nothing (game 14's turn 107, live): the AI's INSPECT check decides.
    ins = ns["bc"].inspect_test_trade(lq.build_test_trade(7, [{"type": "RESOURCE", "name": "RESOURCE_COAL", "amount": 1, "duration": 30}], []))
    check("check Lua: INSPECT, not EQUALIZE, after the mark", "EQUALIZE" not in ins and ins.index("MARK|") < ins.index("DealProposalAction.INSPECT"))
    for verdict, want in (("ACCEPTED", "AI response: ACCEPTABLE"), ("REJECTED", "AI response: NOT ACCEPTABLE as-is"),
                          (None, "AI response: NO ANSWER to its check")):
        GAME = trade(); GAME.conn.test_equal, GAME.conn.inspect_answer = True, verdict
        out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100, mode="test")
        log = GAME.conn.deal_log
        check(f"test, terms unchanged, check {verdict}: {want.split(': ')[1]}", want in out and log.count("inspect") == 1
              and log.index("inspect") > log.index("reread") and log[-2:] == ["poll", "clear"] and "close" in log[log.index("inspect"):],
              (out, log))
    # A finished trade call empties the working deals (game 15: Egypt's refused test deal on turn 95 came back as
    # "Deal from Egypt" with three later statements, and the agent accepted it each time), but never under a session
    # or a deal the civ still holds.
    GAME = trade(test_answer="REJECTED")
    out = await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100, mode="test")
    log = GAME.conn.deal_log
    check("test refused: working deals emptied after the close", log[-1] == "clear" and log.index("clear") > log.index("close"), log)
    GAME = trade(deal_answer="REJECTED")
    await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("proposal refused: working deals emptied", GAME.conn.deal_log[-1] == "clear", GAME.conn.deal_log)
    GAME = trade(deal_leftover="hidden")
    await tool.fn(CTX, other_player_id=7, offer_resources="RESOURCE_COAL", request_gold=100)
    check("a deal the civ still holds: working deals kept", "clear" not in GAME.conn.deal_log, GAME.conn.deal_log)
    clr = ns["bc"].deal_clear_lua(7)
    check("clear Lua: both directions, only with no session and no pending deal", clr.count("ClearWorkingDeal") == 2
          and "DealDirection.INCOMING" in clr and "DealDirection.OUTGOING" in clr
          and clr.index("FindOpenSessionID") < clr.index("ClearWorkingDeal") and "HasPendingDeal(t, me)" in clr, clr)
    # respond_to_trade: the AI's offer is copied into the player's deal before ACCEPTED, as the deal view does.
    rtool = mcp._tool_manager.get_tool("respond_to_trade")
    GAME = trade()
    out = await rtool.fn(CTX, other_player_id=7, accept=True)
    check("accept an AI offer: copied, then accepted", GAME.conn.deal_log[0] == "accept-copy" and out.startswith("DEAL_ACCEPTED|"), (GAME.conn.deal_log, out))
    acc = ns["bc"].deal_accept_lua(7)
    check("accept Lua copies before it sends", acc.index("CopyIncomingToOutgoingWorkingDeal") < acc.index("DealProposalAction.ACCEPTED"))
    GAME = trade()
    out = await rtool.fn(CTX, other_player_id=7, accept=False)
    check("refuse an AI offer", out.startswith("DEAL_REJECTED|Spain"), out)
    GAME = trade(deal_enacts=False); GAME._pending_end_turn = True
    out = await rtool.fn(CTX, other_player_id=7, accept=True)
    check("accept during the AI turns: in effect when they go on", out.startswith("DEAL_ACCEPTED|Accepted: we give")
          and "when they go on" in out, out)
    GAME = trade(deal_enacts=False)
    out = await rtool.fn(CTX, other_player_id=7, accept=True)
    check("accept, no enactment, not during the AI turns: unclear", out.startswith("DEAL_UNCLEAR|"), out)

    # 31. A leader screen that comes up while end_turn waits: civ6-mcp's one InGame probe (45 s of quiet) closes it
    #     first (game 13's turn 108, live), and otherwise does civ6-mcp's own diplomacy check.
    etm = ns["_etm"]
    check("civ6-mcp's end turn calls the mid-turn probe by name", _inspect.getsource(etm).count("await _check_mid_turn_diplomacy(") == 2
          and etm._check_mid_turn_diplomacy is ns["_mid_turn_leader_screen_first"])
    class ScreenConn:
        def __init__(self, reply): self.reply, self.sent = reply, []
        async def execute_write(self, lua, timeout=None):
            self.sent.append(lua); return [self.reply, lq.SENTINEL]
    turns, orig_calls = iter([108, 109]), []
    async def fake_turn(gs): return next(turns)
    async def fake_orig(gs, lua, turn_before): orig_calls.append(turn_before); return ("Turn paused", False)
    saved = (etm._get_turn_number, ns["_original_mid_turn_diplomacy"], ns["asyncio"].sleep, ns["_turn_active"])
    async def no_sleep(_): return None
    active = [False]
    async def fake_active(game): return active[0]
    etm._get_turn_number, ns["_original_mid_turn_diplomacy"], ns["asyncio"].sleep = fake_turn, fake_orig, no_sleep
    ns["_turn_active"] = fake_active
    try:
        gs = types.SimpleNamespace(conn=ScreenConn("LEADER_SCREEN|CLOSED"))
        got = await ns["_mid_turn_leader_screen_first"](gs, "lua", 108)
        check("screen up, no session: closed, the turn went on", got == (None, True) and not orig_calls, (got, orig_calls))
        gs = types.SimpleNamespace(conn=ScreenConn("LEADER_SCREEN|SESSION"))
        got = await ns["_mid_turn_leader_screen_first"](gs, "lua", 108)
        check("a session open: civ6-mcp's own check", got == ("Turn paused", False) and orig_calls == [108], (got, orig_calls))
        # The game refused the turn end over a unit that needs orders (the player's turn is active again).
        class UnitsConn:
            async def execute_write(self, lua, timeout=None):
                if "LEADER_SCREEN" in lua: return ["LEADER_SCREEN|HIDDEN", lq.SENTINEL]
                return ["UNITS_BLOCK", "UNIT|2686988|UNIT_SETTLER|37,42|1/2", lq.SENTINEL]
        active[0] = True
        got = await ns["_mid_turn_leader_screen_first"](types.SimpleNamespace(conn=UnitsConn()), "lua", 100)
        check("turn end refused over a unit: named at the probe, not after 10 minutes",
              got[1] is False and got[0].startswith("The turn did not end") and "UNIT_SETTLER [id:2686988]" in got[0]
              and orig_calls == [108], got)
        active[0] = False
        got = await ns["_mid_turn_leader_screen_first"](types.SimpleNamespace(conn=UnitsConn()), "lua", 100)
        check("AI turns still running: no units check", got == ("Turn paused", False), got)
    finally:
        etm._get_turn_number, ns["_original_mid_turn_diplomacy"], ns["asyncio"].sleep, ns["_turn_active"] = saved
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
    want = [bound] + [ns[w](stock).__code__ for w in ("_reports_escapes", "_names_promotions", "_explores_again",
                                                       "_hang_note", "_units_first")]
    check("end_turn tool: spy escapes, promotions named, explore, hang note, then the units/pending wrapper",
          chain[:6] == want)
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
    # civ6-mcp finds no save to reload (as in the live trade-hang replay): it returns the hang as is, nothing undone.
    steps = ["HANG:96:0_MCP_0096|End turn requested but turn did not advance"]
    async def no_save(ctx=None): return await GameState.end_turn(GAME)
    out = await ns["_hang_note"](no_save)(ctx=CTX)
    check("hang with no reload: says so, claims no reload", "could not be reloaded automatically" in out
          and "was undone" not in out and out.endswith("did not advance"), repr(out[:200]))

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
               "(moves left: 1). The game stopped it there with 1 moves left, " + ns["bc"].SHORT_OF_MOVES),
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
    # 11b. An adjacent attack civ6-mcp reported from its estimate (game 21, turn 40: "est damage dealt:~100" while the
    #      target kept its 100 HP, after a move-and-attack stopped next to it with 1 move left).
    async def adjacent_est(self, ui, tx, ty):
        return (EST + "MELEE_ATTACK|target:UNIT_WARRIOR at (43,45)|enemy HP:41 -> 41/100|your HP:100 -> 100 CS:30"
                "|est damage dealt:~41\n  Post-combat: ~0/41 (estimate — verify with get_units)")
    NEXT = ["ME|43|44|1|100|1", "FOE|UNIT_WARRIOR|41|20"]
    adj_cases = [
        ("refused: says so", [NEXT], 13,
         EST + "Error: NOT_ATTACKED|The game did not carry out the attack: after 6 seconds UNIT_WARRIOR at (43,45) still "
               "has 41 HP, and your unit at (43,44) still has its 1 moves left, " + ns["bc"].SHORT_OF_MOVES
               + " Check get_units before you order it again."),
        ("landed late: real numbers", [NEXT, NEXT, ["ME|43|44|1|81|0", "FOE|UNIT_WARRIOR|9|20"]], 3,
         EST + "MELEE_ATTACK|target:UNIT_WARRIOR at (43,45)|attacked from (43,44)|enemy HP:41 -> 9|your HP:100 -> 81"
               "|moves left: 0"),
        ("killed and advanced", [NEXT, ["ME|43|45|0|95|0"]], 2,
         EST + "MELEE_ATTACK|target:UNIT_WARRIOR at (43,45)|advanced into (43,45)|enemy HP:41 -> killed|your HP:100 -> "
               "95|moves left: 0"),
        ("moves spent, hit points not read yet: estimate kept", [NEXT, ["ME|43|44|1|100|0", "FOE|UNIT_WARRIOR|41|20"]],
         13, None),
    ]
    ns["_original_attack_unit"] = adjacent_est
    for name, states, reads, want in adj_cases:
        g = AttackGame(states)
        out = await attack(g, 9, 43, 45)
        want = want or await adjacent_est(None, 9, 43, 45)
        check(f"adjacent attack: {name}", out == want and g.conn.reads == reads, f"{g.conn.reads} reads: {out!r}")
    check("estimate detection", ns["bc"].melee_estimated(await adjacent_est(None, 9, 43, 45))
          and not ns["bc"].melee_estimated(await adjacent(None, 9, 43, 45)))
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

    # 16b. A spy that travelled has a new id: not "killed" (game 19, turns 197 and 203).
    before = TurnSnapshot(turn=196, units={10: U(10, "Raheem", "UNIT_SPY", 39, 33), 11: U(11, "Uday", "UNIT_SPY", 39, 33),
                                           12: U(12, "Warrior", "UNIT_WARRIOR", 40, 40)},
                          cities={}, current_research="", current_civic="")
    after = TurnSnapshot(turn=197, units={20: U(20, "Raheem", "UNIT_SPY", 50, 30)}, cities={}, current_research="",
                         current_civic="")
    msgs = {e.message: e.priority for e in GameState._diff_snapshots(before, after)}
    check("spy listed again under its name: moved, new id",
          msgs.get("Your spy Raheem moved from (39,33) to (50,30) and has a new id, 20.") == 2, msgs)
    check("spy not listed: not called killed, get_spies named",
          any(m.startswith("Your spy Uday is no longer listed") and "get_spies" in m for m in msgs)
          and not any("Uday (UNIT_SPY) was killed" in m for m in msgs), msgs)
    check("other units are still 'killed'", msgs.get("Your Warrior (UNIT_WARRIOR) was killed! Last seen at (40,40).") == 1)

    # 16c. Spy travel: the game's reasons instead of "Allied civ cities are not valid" (game 19, 3 refusals).
    bc = ns["bc"]
    check("spy travel builder replaced", lq.build_spy_travel is bc.spy_travel_lua)
    lua = lq.build_spy_travel(19, 57, 14)
    check("spy travel: same op and params as civ6-mcp's",
          "UNITOPERATION_SPY_TRAVEL_NEW_CITY" in lua and bc.op_hash("UNITOPERATION_SPY_TRAVEL_NEW_CITY") == -1295211657
          and "PARAM_X0] = x" in lua and "GetUnit(me, 19)" in lua and "local x, y = 57, 14" in lua)
    check("spy travel: refusal gives reasons, moves and the city", "res[UnitOperationResults.FAILURE_REASONS]" in lua and "GetMovesRemaining" in lua
          and "Cities.GetPlotPurchaseCity(x, y)" in lua and "Allied civ" not in lua)
    spy_doc = mcp._tool_manager.get_tool("spy_action").description
    check("spy_action description: other civs' cities are targets",
          "other civs' cities" in spy_doc and "Allied civ cities are NOT" not in spy_doc
          and "own cities and city-states only" not in spy_doc and "queued end-of-turn" in spy_doc, spy_doc[-700:])
    out = bc.filter_output("  Travel: spy_action(unit_id, action='travel', target_x, target_y) — send spy to own city "
                           "or city-state", bc.OUTPUT_RULES["get_spies"])
    check("get_spies: travel line fixed", out.endswith("send spy to a city: your own, a city-state's or another civ's"), out)

    # 16d. Pillage: unit_action sends the game's own order and reads the tile back.
    ua = mcp._tool_manager.get_tool("unit_action")
    check("unit_action description names pillage", "pillage = pillage what is on the unit's own tile" in ua.description)
    lua = bc.pillage_lua(7, "UNITOPERATION_PILLAGE")
    check("pillage: the game's op on the unit's tile, reasons on refusal",
          "UnitOperations['UNITOPERATION_PILLAGE']" in lua and "PARAM_X] = x" in lua and "res[UnitOperationResults.FAILURE_REASONS]" in lua
          and "RequestOperation(unit, op.Hash, params)" in lua and "OK:PILLAGE_SENT" in lua)
    check("pillage tile read: districts, buildings, improvement, road",
          all(k in bc.pillage_tile_lua(7) for k in ("IsImprovementPillaged", "d:IsPillaged()", "IsPillaged(b.Index)",
                                                     "IsRoutePillaged")))
    class PillageConn:
        def __init__(self, tiles): self.tiles, self.sent = list(tiles), []
        async def execute_write(self, lua, timeout=None):
            if "PILLAGE_SENT" in lua:
                self.sent.append(lua); return ["OK:PILLAGE_SENT|50|28", lq.SENTINEL]
            return [self.tiles.pop(0) if len(self.tiles) > 1 else self.tiles[0], lq.SENTINEL]
    saved = GAME
    GAME = types.SimpleNamespace(conn=PillageConn(["TILE|50|28|2|DISTRICT_SPACEPORT=intact",
                                                    "TILE|50|28|0|DISTRICT_SPACEPORT=pillaged,ROAD=intact"]))
    out = await ua.fn(CTX, unit_id=65543, action="pillage")
    check("pillage: reports the tile once it reads pillaged", out.startswith("PILLAGE_SENT|pillage at (50,28)")
          and "DISTRICT_SPACEPORT=pillaged, ROAD=intact" in out and "moves left: 0" in out
          and "GetUnit(me, 7)" in GAME.conn.sent[0], out)
    class RefuseConn:
        async def execute_write(self, lua, timeout=None):
            return ["ERR:CANNOT_PILLAGE|The game refused UNITOPERATION_PILLAGE_ROUTE at (1,2): no road. The unit has 1 moves left.",
                    lq.SENTINEL]
    GAME = types.SimpleNamespace(conn=RefuseConn())
    out = await ua.fn(CTX, unit_id=7, action="pillage_route")
    check("pillage refused: the game's reasons", out.startswith("Error: CANNOT_PILLAGE|") and "no road" in out, out)
    GAME = saved
    seen_actions = []
    async def inner(ctx=None, unit_id=None, action=None, **k):
        seen_actions.append(action); return "FORTIFIED"
    out = await ns["_pillages"](inner)(ctx=CTX, unit_id=7, action="fortify")
    check("other actions pass through", out == "FORTIFIED" and seen_actions == ["fortify"], out)

    # 16h. A refused trade route gives the game's reasons (game 20, turn 146: one Trader refused everywhere).
    lua = lq.build_make_trade_route(18, 35, 17)
    i = lua.index("ERR:CANNOT_START_ROUTE")
    check("trade route: refusal gives reasons and the Trader's city", "res[UnitOperationResults.FAILURE_REASONS]" in lua
          and "The game will not start this route to (35,17)" in lua and "returned false" not in lua
          and "CityManager.GetCityAt(unit:GetX(), unit:GetY())" in lua and lua.count("UnitManager.RequestOperation") == 1
          and "ERR:CAPACITY_FULL" in lua)

    # 16i. A city's CAN ATTACK list is the game's own target list (game 20: a Builder on turn 77, units of a civ at
    # peace on turn 172).
    lua = lq.build_cities_query()
    check("city attack list: the game's own targets",
          "CityManager.GetCommandTargets(c, CityCommandTypes.RANGE_ATTACK)" in lua
          and "if wallMax > 0 then\n        local cx, cy = c:GetX(), c:GetY()" not in lua
          and lua.count("local cityTargets = {}") == 1 and lua.count("local pillDistricts = {}") == 1
          and "table.concat(cityTargets" in lua and "__benchRes(plot)" in lua
          and "dip:IsAtWarWith(o)" in lua and "FORMATION_CLASS_CIVILIAN" in lua)

    # 16j. send_envoy says how many envoys are left (game 20, turns 152 and 173: an end turn refused over the second).
    lua = lq.build_send_envoy(15)
    check("send_envoy: counts envoys before the request",
          lua.index("local __left = pInfluence:GetTokensToGive() - 1") < lua.index("UI.RequestPlayerOperation")
          and "to give this turn: send them before end_turn" in lua and lua.count("OK:ENVOY_SENT") == 1)

    class _Envoy:
        conn = None
    async def vendor_envoy(self, pid):
        return f"OK:ENVOY_SENT|Mohenjo-Daro. 1 more envoy to give this turn: send them before end_turn (verified remaining: 2)"
    ns_vendor = ns["_vendor_send_envoy"]
    ns["_vendor_send_envoy"] = vendor_envoy
    try:
        out = await ns["_send_envoy_count"](_Envoy(), 15)
    finally:
        ns["_vendor_send_envoy"] = ns_vendor
    check("send_envoy: the stale re-read is dropped", out.endswith("send them before end_turn"), out)

    # 16k. Settle scans leave out tiles another civ owns (game 20, turn 182: a site inside Spain's borders).
    for name, lua in (("settle advisor", lq.build_settle_advisor_query(5)), ("global settle scan", lq.build_global_settle_scan())):
        check(f"{name}: no sites on another civ's land",
              lua.count("(cPlot:GetOwner() == -1 or cPlot:GetOwner() == me) then") == 1 and "local me = " in lua)

    # 16l. end_turn passes on the escape route civ6-mcp picked for a discovered spy (game 21, turns 132 and 156).
    note = ns["bc"].escape_note(["Auto-resolved spy escape: OK:ESCAPE_ROUTE|Sherzi escaping via DISTRICT_CITY_CENTER",
                                 "Auto-resolved spy escape: OK:ESCAPE_ROUTE|Hakim escaping via DISTRICT_COMMERCIAL_HUB"])
    check("escape note: names each spy and route", note.startswith("Spy escape: Your spy Sherzi was discovered")
          and "chose the City Center" in note and "Hakim" in note and "chose the Commercial Hub" in note
          and "game's roll" in note, note)
    check("escape note: nothing without a pick", ns["bc"].escape_note(["Auto-resolved spy escape: ERR:NO_CITY"]) == "")
    async def ending_turn(*a, **k):
        logging.getLogger("civ_mcp.end_turn").info("Auto-resolved spy escape: %s",
                                                   "OK:ESCAPE_ROUTE|Sherzi escaping via DISTRICT_CITY_CENTER")
        return "Turn 132 -> 133 | Score: 233"
    async def quiet_turn(*a, **k): return "Turn 133 -> 134 | Score: 234"
    _lvl = logging.getLogger("civ_mcp.end_turn").level
    logging.getLogger("civ_mcp.end_turn").setLevel(logging.INFO)
    try:
        out = await ns["_reports_escapes"](ending_turn)()
        out2 = await ns["_reports_escapes"](quiet_turn)()
    finally:
        logging.getLogger("civ_mcp.end_turn").setLevel(_lvl)
    check("end_turn: escape note after the report", out.startswith("Turn 132 -> 133 | Score: 233\n\nSpy escape: Your spy "
          "Sherzi") and out2 == "Turn 133 -> 134 | Score: 234", repr(out))

    # 16m. No going back (game 22, turn 204: Sonnet loaded its turn-200 save after a government switch left it in Anarchy).
    bcx = ns["bc"]
    check("save turn from the name", bcx.save_turn("0_MCP_0200") == 200 and bcx.save_turn("AutoSave_0023") == 23
          and bcx.save_turn("BENCH_PANGAEA_ONLINE_T1") is None)
    check("result turn: end_turn and overview", bcx.turn_in_result("Turn 222 -> 223 | Score: 471") == 223
          and bcx.turn_in_result("Turn 204 | Sumeria (Gilgamesh) | Score: 442") == 204
          and bcx.turn_in_result("Turn 132 ended while you answered the AI civ ...\n\nTurn 132 -> 133 | Score") == 133
          and bcx.turn_in_result("MOVING_TO|40,32") is None)
    check("earlier save refused", bcx.earlier_turn_refusal("0_MCP_0200", 204).startswith("Error: EARLIER_TURN|0_MCP_0200 "
          "is from turn 200, and this game has reached turn 204.") and "AutoSave_0204" in bcx.earlier_turn_refusal("0_MCP_0200", 204))
    check("current-turn saves allowed", bcx.earlier_turn_refusal("AutoSave_0204", 204) == ""
          and bcx.earlier_turn_refusal("0_MCP_0204", 204) == "" and bcx.earlier_turn_refusal(None, 204) == "")
    check("before the first turn anything loads", bcx.earlier_turn_refusal("AutoSave_0001", 1) == ""
          and bcx.earlier_turn_refusal("BENCH_PANGAEA_ONLINE_T1", 0) == "")
    check("a named save mid-game refused", "is not a save of a turn of this game" in
          bcx.earlier_turn_refusal("BENCH_PANGAEA_ONLINE_T1", 50))
    check("list_saves index resolved", bcx.save_at_index("Available saves (filesystem scan, sorted by date):\n"
          "  1. 0_MCP_0204\n  2. AutoSave_0204\n  9. 0_MCP_0200\n", 9) == "0_MCP_0200"
          and bcx.save_at_index("  1. 0_MCP_0204\n", 3) is None)
    _saved_path, _saved_run = ns["_TOP_TURN_PATH"], ns["srv"].heartbeat._run_id
    _tmpdir = tempfile.mkdtemp()
    ns["_TOP_TURN_PATH"] = os.path.join(_tmpdir, "top_turn.json")
    ns["srv"].heartbeat._run_id = "g99-test"
    try:
        ns["_note_turn"]("Turn 203 -> 204 | Score: 442")
        ns["_note_turn"]("Turn 200 | Sumeria")  # a lower turn never lowers it
        loads = []
        async def fake_load(ctx=None, save_name=None): loads.append(save_name); return "Loaded " + save_name
        guarded = ns["_no_going_back"](fake_load)
        out1 = await guarded(ctx=None, save_name="0_MCP_0200")
        out2 = await guarded(ctx=None, save_name="AutoSave_0204")
        check("guard: refuses turn 200 at turn 204, loads turn 204", out1.startswith("Error: EARLIER_TURN|")
              and out2 == "Loaded AutoSave_0204" and loads == ["AutoSave_0204"] and ns["_top_turn"]() == 204, (out1, loads))
        ns["srv"].heartbeat._run_id = "g100-next"
        check("guard: a new run starts from 0", ns["_top_turn"]() == 0)
    finally:
        ns["_TOP_TURN_PATH"], ns["srv"].heartbeat._run_id = _saved_path, _saved_run
        shutil.rmtree(_tmpdir, ignore_errors=True)
    for _n in ("load_game_save", "restart_and_load", "load_save", "load_save_from_menu"):
        _t = mcp._tool_manager.get_tool(_n)
        check(f"{_n}: guarded and described", _t.fn.__wrapped__.__code__ is ns["_no_going_back"](stock).__code__
              and "does not go back" in _t.description, _n)

    # 16n. Government changes checked as the game's Government screen does (game 22, turn 203: back to Classical
    # Republic, Anarchy, and the agent took it for a bug).
    st = bcx.parse_gov_state(["junk", "GOVSTATE|203|8|false|-1|true|false|true|3|true|Classical Republic|Professional Sports"])
    check("gov state parsed", st == {"turn": 203, "current": 8, "anarchy": False, "anarchy_end": -1, "civic_done": True,
          "change_made": False, "can_at_all": True, "anarchy_turns": 3, "usable": True, "name": "Classical Republic",
          "civic": "Professional Sports"}, st)
    check("gov state: missing or short is None", bcx.parse_gov_state(["OK"]) is None
          and bcx.parse_gov_state(["GOVSTATE|1|2"]) is None)
    warn = bcx.gov_change_refusal(st, "GOVERNMENT_CLASSICAL_REPUBLIC", False)
    check("back to a government had before: warned first", warn.startswith("Error: ANARCHY_WARNING|You have had "
          "Classical Republic before") and "3 turns of Anarchy" in warn and "again this turn" in warn, warn)
    check("confirmed on the same turn: allowed", bcx.gov_change_refusal(st, "GOVERNMENT_CLASSICAL_REPUBLIC", True) == "")
    new = dict(st, anarchy_turns=0)
    check("a government never had: allowed", bcx.gov_change_refusal(new, "GOVERNMENT_COMMUNISM", False) == "")
    no_civic = bcx.gov_change_refusal(dict(new, civic_done=False), "GOVERNMENT_COMMUNISM", True)
    check("no civic this turn: refused, next chance named", no_civic.startswith("Error: GOV_CHANGE_NOT_NOW|No civic was "
          "completed this turn.") and "Professional Sports, completes" in no_civic, no_civic)
    check("no civic in progress: says pick one", "choose one with set_research" in
          bcx.gov_change_refusal(dict(new, civic_done=False, civic=""), "GOVERNMENT_COMMUNISM", False))
    twice = bcx.gov_change_refusal(dict(new, change_made=True), "GOVERNMENT_COMMUNISM", False)
    check("second change in a turn: refused", twice.startswith("Error: GOV_CHANGE_NOT_NOW|You already changed "
          "government this turn.") and "next chance" not in twice, twice)
    anarchy = dict(new, anarchy=True, anarchy_end=206, current=-1)
    check("during Anarchy: refused with its end", bcx.gov_change_refusal(anarchy, "GOVERNMENT_COMMUNISM", True)
          .startswith("Error: IN_ANARCHY|Your civilization is in Anarchy until turn 206"))
    check("unknown state: civ6-mcp decides", bcx.gov_change_refusal(None, "GOVERNMENT_X", False) == "")
    check("not unlocked or current: civ6-mcp says which", bcx.gov_change_refusal(dict(new, usable=False, civic_done=False),
          "GOVERNMENT_AUTOCRACY", False) == "")
    check("no change at all now: the rule alone", bcx.gov_change_refusal(dict(new, can_at_all=False), "GOVERNMENT_COMMUNISM",
          False).startswith("Error: GOV_CHANGE_NOT_NOW|The game allows a government change only on a turn"))
    check("after note: Anarchy and its end", bcx.gov_after_note(anarchy).startswith(". ANARCHY until turn 206")
          and bcx.gov_after_note(new) == "" and bcx.gov_after_note(None) == "")
    # 16o. War declarations settled by the war state read after them (game 24: all 9 came back WAR_UNCERTAIN, and
    # the one on America on turn 115 had not taken effect).
    uncertain = ("WARN:WAR_UNCERTAIN|DECLARE_SURPRISE_WAR session completed but war state not yet confirmed for "
                 "America. Check next turn.")
    ws = bcx.parse_war_state(["junk", "WARSTATE|true|America"])
    check("war state parsed", ws == {"at_war": True, "name": "America"}, ws)
    check("war state: missing or bad is None", bcx.parse_war_state(["OK"]) is None
          and bcx.parse_war_state(["WARSTATE|maybe|America"]) is None)
    check("war on: OK", bcx.war_result(uncertain, ws).startswith("OK:WAR_DECLARED|At war with America"))
    check("still peace: needs another look", bcx.war_result(uncertain, {"at_war": False, "name": "America"}) == "")
    check("other answers and unknown state: civ6-mcp's", bcx.war_result("ERR:ALREADY_AT_WAR|x", ws) == "ERR:ALREADY_AT_WAR|x"
          and bcx.war_result(uncertain, None) == uncertain)
    check("war Lua: the player id only", "local t = 5 " in bcx.war_state_lua(5) and "IsAtWarWith(t)" in bcx.war_state_lua(5))

    class WarConn:
        def __init__(self, states): self.states, self.reads = list(states), 0
        async def execute_write(self, lua, timeout=None):
            self.reads += 1
            return [f"WARSTATE|{self.states.pop(0)}|America", "---END---"]

    class WarGame:
        def __init__(self, states): self.conn = WarConn(states)

    _vendor_diplo, _sleep = ns["_vendor_send_diplomatic_action"], ns["asyncio"].sleep
    async def fake_diplo(self, other, action):
        return uncertain if action.upper().startswith("DECLARE_") else "OK:SENT|DENOUNCE sent to America"
    async def no_sleep(s): return None
    ns["_vendor_send_diplomatic_action"], ns["asyncio"].sleep = fake_diplo, no_sleep
    try:
        g1, g2, g3 = WarGame(["true"]), WarGame(["false", "true"]), WarGame(["false", "false"])
        r1 = await GameState.send_diplomatic_action(g1, 5, "DECLARE_SURPRISE_WAR")
        r2 = await GameState.send_diplomatic_action(g2, 5, "DECLARE_SURPRISE_WAR")
        r3 = await GameState.send_diplomatic_action(g3, 5, "declare_surprise_war")
        g4 = WarGame([])
        r4 = await GameState.send_diplomatic_action(g4, 5, "DENOUNCE")
    finally:
        ns["_vendor_send_diplomatic_action"], ns["asyncio"].sleep = _vendor_diplo, _sleep
    check("declaration: war on at the first look", r1.startswith("OK:WAR_DECLARED|") and g1.conn.reads == 1, r1)
    check("declaration: war on at the second look", r2.startswith("OK:WAR_DECLARED|") and g2.conn.reads == 2, r2)
    check("declaration: still peace says send again", r3.startswith("Error: WAR_NOT_DECLARED|The game still shows "
          "peace with America") and "DECLARE_SURPRISE_WAR did not take effect" in r3 and g3.conn.reads == 2, r3)
    check("other actions: untouched", r4 == "OK:SENT|DENOUNCE sent to America" and g4.conn.reads == 0, r4)

    # 16p. set_research / set_civic ask the game's own CanResearch / CanProgress before the request (game 25: Economics
    # set through GameCore on turn 115 before its prerequisites, reset by the game the next turn).
    for _b, _n, _can in ((lq.build_set_research, "TECH_ECONOMICS", "GetTechs():CanResearch(idx)"),
                         (lq.build_set_research_gamecore, "TECH_ECONOMICS", "GetTechs():CanResearch(idx)"),
                         (lq.build_set_civic, "CIVIC_HUMANISM", "GetCulture():CanProgress(idx)"),
                         (lq.build_set_civic_gamecore, "CIVIC_HUMANISM", "GetCulture():CanProgress(idx)")):
        _r = bcx.base_game_rewrite(_b(_n), "-- prelude")
        _i, _j = _r.find("ALREADY_COMPLETED"), _r.find("ERR:NOT_AVAILABLE|" + _n)
        _k = max(_r.find("UI.RequestPlayerOperation"), _r.find("SetResearchingTech(idx)"), _r.find("SetProgressingCivic(idx)"))
        check(f"{_b.__name__}: availability asked after the done check, before the request", _r.count("NOT_AVAILABLE") == 1
              and _can in _r and 0 < _i < _j < _k, _r[_i:_i + 200])

    lua = bcx.gov_state_lua("GOVERNMENT_COMMUNISM")
    check("state Lua: anarchy turns read only outside Anarchy", "if usable and not an then" in lua
          and "GetAnarchyTurns(row.Index)" in lua and "GameInfo.Governments['GOVERNMENT_COMMUNISM']" in lua)
    check("state Lua: a bad name is not pasted in", "Governments['']" in bcx.gov_state_lua("X'] os.exit() --"))
    calls, warned_turn = [], {"t": 203}

    class FakeConn:
        async def execute_write(self, lua, timeout=None):
            calls.append("state" if "GOVSTATE" in lua else "other")
            return [f"GOVSTATE|{warned_turn['t']}|3|false|-1|true|false|true|3|true|Classical Republic|Space Race"]

    class FakeGame:
        conn = FakeConn()

    _vendor = ns["_vendor_change_government"]
    changed = []
    async def fake_vendor(self, g): changed.append(g); return "GOVERNMENT_CHANGED|" + g + "|Classical Republic"
    ns["_vendor_change_government"] = fake_vendor
    try:
        r1 = await GameState.change_government(FakeGame(), "GOVERNMENT_CLASSICAL_REPUBLIC")
        r2 = await GameState.change_government(FakeGame(), "government_classical_republic")
        warned_turn["t"] = 204
        ns["_anarchy_warned"].clear()
        r3 = await GameState.change_government(FakeGame(), "GOVERNMENT_CLASSICAL_REPUBLIC")
    finally:
        ns["_vendor_change_government"] = _vendor
    check("change_government: warns, then switches on the second call", r1.startswith("Error: ANARCHY_WARNING|")
          and r2.startswith("GOVERNMENT_CHANGED|") and changed == ["government_classical_republic"]
          and r3.startswith("Error: ANARCHY_WARNING|"), (r1, r2, r3, changed))
    _t = mcp._tool_manager.get_tool("change_government")
    check("change_government: description says the game's rules", "First switch after" not in _t.description
          and "at least 3 turns of Anarchy" in _t.description, _t.description)

    # 16g. Attacks on a city with no unit in it (game 20, turn 58: Salvador, "No hostile unit at (42,35)").
    lua = lq.build_attack_unit(13, 42, 35)
    check("attack builder replaced", lq.build_attack_unit.__qualname__.startswith("attack_lua"))
    check("attack: city centre or Encampment taken as the target", "DISTRICT_GARRISON" in lua
          and "Players[owner]:GetDistricts():Members()" in lua and "enemyName = di.DistrictType" in lua
          and lua.index("DISTRICT_GARRISON") < lua.index("No hostile unit or city at (42,35)")
          and lua.index("No hostile unit or city at") < lua.index("IsAtWarWith(enemyOwner)"))
    check("attack: an undefended district says pillage", "has no defences to attack" in lua and "unit_action pillage" in lua)
    check("attack: unchanged when civ6-mcp's text moves", bc.attack_lua(lambda u, x, y: "print('x')")(1, 2, 3) == "print('x')")
    rep = bc.city_attack_report("MELEE_ATTACK|target:DISTRICT_CITY_CENTER of Salvador at (42,35)|enemy HP:200 -> 200/200|"
                                "your HP:100 -> 100 CS:30|damage dealt:200 (killed)\n  Post-combat: Target eliminated",
                                "DEF|3|false|156/200|0/0")
    check("city attack report: hit points read after, no 'killed'", "enemy HP:200 -> 156/200" in rep and "killed" not in rep
          and "Target eliminated" not in rep and "garrison 156/200, walls 0/0" in rep, rep)
    rep = bc.city_attack_report("MELEE_ATTACK|target:DISTRICT_CITY_CENTER of Salvador at (42,35)|enemy HP:20 -> 20/200|"
                                "your HP:90 -> 90 CS:30|damage dealt:20 (killed)\n  Post-combat: Target eliminated",
                                "DEF|0|true|0/200|0/0")
    check("city attack report: a taken city", "the city is yours" in rep and "enemy HP:20 -> taken" in rep, rep)
    class DefConn:
        def __init__(self): self.sent = []
        async def execute_write(self, lua, timeout=None):
            self.sent.append(lua)
            return ["DEF|3|false|120/200|0/0", lq.SENTINEL] if lua.startswith("local me") and "DEF|" in lua else [lq.SENTINEL]
    saved_atk = ns["_vendor_attack_unit"]
    async def fake_atk(self, u, x, y):
        return "MELEE_ATTACK|target:DISTRICT_CITY_CENTER of Salvador at (42,35)|enemy HP:156 -> 156/200|damage dealt:156 (killed)\n  Post-combat: Target eliminated"
    ns["_vendor_attack_unit"] = fake_atk
    try:
        g = types.SimpleNamespace(conn=DefConn())
        rep = await ns["_attack_unit_districts"](g, 13, 42, 35)
        check("attack_unit: district target read back", "enemy HP:156 -> 120/200" in rep and "garrison 120/200" in rep, rep)
        async def unit_atk(self, u, x, y): return "MELEE_ATTACK|target:UNIT_WARRIOR at (1,2)|enemy HP:100 -> KILLED"
        ns["_vendor_attack_unit"] = unit_atk
        g = types.SimpleNamespace(conn=DefConn())
        rep = await ns["_attack_unit_districts"](g, 13, 1, 2)
        check("attack_unit: unit targets unchanged", rep.endswith("KILLED") and g.conn.sent == [], rep)
    finally:
        ns["_vendor_attack_unit"] = saved_atk

    before = ((41, 36, 1, 100, 4), ("DISTRICT_CITY_CENTER of Salvador", 200, -1))
    rep = ns["_attack_report"](before, ((41, 35, 1, 77, 0), ("DISTRICT_CITY_CENTER of Salvador", 156, -1)), 42, 35, 1.0)
    check("move-and-attack on a city: its hit points and the rule", "target:DISTRICT_CITY_CENTER of Salvador" in rep
          and "enemy HP:200 -> 156" in rep and "falls to a melee unit's attack" in rep, rep)
    rep = ns["_attack_report"](before, ((42, 35, 0, 70, 0), None), 42, 35, 1.0)
    check("move-and-attack on a city: taken", "enemy HP:200 -> taken" in rep and "advanced into (42,35)" in rep, rep)
    sl = ns["_attack_state_lua"](13, 42, 35)
    check("move-and-attack reads a city with no unit", "if not any and ow >= 0" in sl and "'|-1'" in sl)

    # 16f. A dropped end-turn request is sent again (game 19, turn 86, replayed: the turn stayed open, nothing blocked
    #      it, and a second request ended it at once).
    check("end-turn Lua is marked for the watcher", lq.build_end_turn().startswith(ns["_END_TURN_MARK"])
          and "UI.RequestAction(ActionTypes.ACTION_ENDTURN)" in lq.build_end_turn())
    class WatchConn:
        def __init__(self, states, resend="RESENT"):
            self.states, self.resend, self.resent, self.sent = list(states), resend, 0, []
        async def execute_read(self, lua, timeout=None):
            turn, active = self.states[0] if len(self.states) == 1 else self.states.pop(0)
            if "TURN|" in lua: return [f"TURN|{turn}", lq.SENTINEL]
            if "IsTurnActive" in lua: return [f"ACTIVE|{str(active).lower()}", lq.SENTINEL]
            return [lq.SENTINEL]
    saved_write = ns["_original_conn_write"]
    async def fake_write(conn, lua, *a, **k):
        conn.sent.append(lua)
        if lua == ns["_RESEND_LUA"]:
            conn.resent += 1
            if conn.resend == "RESENT": conn.states = [(86, False)]  # the second request takes
            return [conn.resend, lq.SENTINEL]
        return ["OK:TURN_ENDED", lq.SENTINEL]
    ns["_original_conn_write"] = fake_write
    try:
        # dropped: turn 86 stays open through both checks, then the resend ends it
        c = WatchConn([(86, True)] * 4)
        check("dropped request: sent again once", await ns["_resend_if_dropped"](c, 86) == 1 and c.resent == 1, c.resent)
        # taken: the AI civs are moving (player's turn inactive)
        c = WatchConn([(86, False)])
        check("request taken: nothing sent", await ns["_resend_if_dropped"](c, 86) == 0 and c.sent == [])
        # a fast turn: the number changed and turn 87 is active; never end the new turn
        c = WatchConn([(87, True)])
        check("next turn already open: nothing sent", await ns["_resend_if_dropped"](c, 86) == 0 and c.sent == [])
        # a blocker holds the turn: asked once, nothing resent
        c = WatchConn([(86, True)], resend="BLOCKED")
        check("blocked turn: no request sent", await ns["_resend_if_dropped"](c, 86) == 0 and c.resent == 1)
        check("resend asks the game's own end-turn checks first", "UI.CanEndTurn()" in ns["_RESEND_LUA"]
              and "NO_ENDTURN_BLOCKING" in ns["_RESEND_LUA"])
        # a unit holds the turn (game 20: 8 refusals, ~70 s each): flagged, and end_turn.py's poll waits end at once
        ev = ns["_refusal_event"]()
        ev.clear()
        c = WatchConn([(86, True)], resend="BLOCKED|UNITS")
        check("units refusal: flagged, nothing resent", await ns["_resend_if_dropped"](c, 86) == 0 and c.resent == 1
              and ev.is_set())
        check("resend Lua names a units refusal", "ENDTURN_BLOCKING_UNITS then print('BLOCKED|UNITS')" in ns["_RESEND_LUA"])
        clock = type(ns["_etm"].asyncio)
        check("end_turn.py uses the clock", isinstance(ns["_etm"].asyncio, clock) and clock.__name__ == "_EndTurnAsyncio")
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        r = await clock.sleep(30.0, "x")
        check("flagged: a 30 s poll wait ends at once", loop.time() - t0 < 0.5 and r == "x", loop.time() - t0)
        c = WatchConn([(86, True), (86, False)])
        await ns["_write_watching_end_turn"](c, lq.build_end_turn())
        await asyncio.gather(*list(ns["_WATCHERS"]))
        check("a new end-turn request clears the flag", not ev.is_set())
        t0 = loop.time()
        await clock.sleep(2.2)
        check("not flagged: the poll wait runs its time", loop.time() - t0 >= 2.1, loop.time() - t0)
        ev.set()
        class NoScreen:
            async def execute_write(self, lua, timeout=None): return [lq.SENTINEL]
        saved_active, saved_orig = ns["_turn_active"], ns["_original_mid_turn_diplomacy"]
        async def inactive(game): return False
        async def orig(gs, lua, tb): return None, False
        ns["_turn_active"], ns["_original_mid_turn_diplomacy"] = inactive, orig
        try:
            await ns["_mid_turn_leader_screen_first"](types.SimpleNamespace(conn=NoScreen()), "", 86)
        finally:
            ns["_turn_active"], ns["_original_mid_turn_diplomacy"] = saved_active, saved_orig
        check("the probe clears the flag", not ev.is_set())
        # the connection wrapper reads the turn before the request, then watches
        c = WatchConn([(86, True), (86, False)])
        out = await ns["_write_watching_end_turn"](c, lq.build_end_turn())
        await asyncio.gather(*list(ns["_WATCHERS"]))
        check("end-turn write: sent once, watcher saw the AI move", out[0] == "OK:TURN_ENDED" and c.resent == 0
              and len(c.sent) == 1, c.sent)
        c = WatchConn([(86, True)])
        await ns["_write_watching_end_turn"](c, "print('x')")
        check("other writes are not watched", not ns["_WATCHERS"] and c.sent == ["print('x')"])
    finally:
        ns["_original_conn_write"] = saved_write

    # 16e. The second hang of one turn names the save of the turn before (game 19, turn 86: 4 hangs).
    ns["_HANGS"].clear()
    async def hang_once(ctx=None):
        r = await GameState.end_turn(GAME)
        while r.startswith("HANG:"): r = await GameState.end_turn(GAME)
        return r
    notes = []
    for _ in range(2):
        steps = ["HANG:86:0_MCP_0086|x", "Cannot end turn — resolve these blockers: units"]
        async def scripted2(self): return steps.pop(0)
        ns["_original_gs_end_turn"] = scripted2
        notes.append(await ns["_hang_note"](hang_once)(ctx=CTX))
    check("first hang of a turn: no advice to go back", "load_game_save" not in notes[0], notes[0][:300])
    check("second hang: load the turn before", 'load_game_save("0_MCP_0085"), then play turn 85 again' in notes[1]
          and "Turn 86 has now hung 2 times" in notes[1], notes[1][:900])

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
