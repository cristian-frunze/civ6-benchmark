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
    import civ_mcp.lua.espionage as _esp  # noqa: E402

    _esp._SPY_OP_HASHES.update(bc.SPY_OPS)  # the builders read the table at call time
    _spy = mcp._tool_manager.get_tool("spy_action")
    _spy.description = bc.SPY_MISSION_LIST.sub(bc.SPY_MISSIONS, _spy.description) + bc.SPY_NOTE
    _spy.description = bc.SPY_TRAVEL_DOC[0].sub(lambda m: bc.SPY_TRAVEL_DOC[1], _spy.description)
    import civ_mcp.lua as _lqs  # noqa: E402

    _lqs.build_spy_travel = bc.spy_travel_lua  # GameState.spy_travel looks it up at call time

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

    # A leader screen left open with no diplomacy session stalls the AI turns (bench_compat.LEADER_SCREEN_LUA). The
    # close can take more than one try: a view still finishing its conversation only fades to the overview at first.
    async def _close_idle_leader_screen(ctx, wait=0.0):
        if wait:
            await asyncio.sleep(wait)  # the engine closes the session a frame later
        for _ in range(3):
            try:
                lines = await srv._get_game(ctx).conn.execute_write(bc.LEADER_SCREEN_LUA, timeout=10.0)
            except Exception:
                logging.getLogger("civ_mcp_http").warning("leader screen check failed", exc_info=True)
                return
            if "LEADER_SCREEN|CLOSED" not in lines:
                if "LEADER_SCREEN|SESSION" in lines:
                    logging.getLogger("civ_mcp_http").info("Leader screen up with a diplomacy session open: left alone")
                return
            logging.getLogger("civ_mcp_http").info("Closed a leader screen left open with no diplomacy session")
            await asyncio.sleep(1.0)
        logging.getLogger("civ_mcp_http").warning("The leader screen was still open after 3 attempts to close it")

    def _then_close_leader_screen(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            out = await fn(*args, **kwargs)
            ctx = kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)
            await _close_idle_leader_screen(ctx, wait=1.0)
            return out

        return wrapper

    # Trades hung the next end turn (games 1-8: 14 of 23 end turns after a propose_trade hung, 3 of 1,600 after
    # turns with no diplomacy). The diplomacy screen locks the engine's event queue when it opens
    # (UI.ReferenceCurrentEvent in DiplomacyActionView.lua) and releases the lock only when it closes. A session the
    # player started does not close the screen: it goes back to the overview, and the game closes it when the
    # player's turn ends, but only if it is visible. civ6-mcp's propose_trade hid it instead, so nothing ever closed
    # it, the AI turns stalled behind the lock, and civ6-mcp reloaded the turn after ~10 minutes, undoing it. Here
    # propose_trade leaves the screen up and the leader-screen check closes it, which releases the lock.
    from civ_mcp import game_state as _gsm  # noqa: E402
    from civ_mcp import lua as _lq  # noqa: E402

    # The trade calls wait for the AI's answer before they accept or close (bench_compat.DEAL_LISTENER has why).
    from civ_mcp.lua.diplomacy import _lua_deal_item  # noqa: E402
    from civ_mcp.narrate import narrate_test_trade  # noqa: E402

    _DEAL_ANSWER_S = 6.0  # the AI answered within a second in the live tests
    _TEST_ACCEPTABLE = "AI response: ACCEPTABLE — this deal would be accepted as-is"  # civ6-mcp's narrate_test_trade
    _dlog = logging.getLogger("civ_mcp_http")

    def _deal_field(lines, key):
        return next((ln.split("|", 1)[1] for ln in lines if ln.startswith(key + "|")), None)

    async def _deal_wait(conn, target, mark, until, timeout=_DEAL_ANSWER_S):
        """Poll the deal events after mark until until(events) returns something, or the timeout. Returns that value
        (None on timeout) and the last STATE fields: session, pending(me,t), pending(t,me), incoming item count."""
        t0 = asyncio.get_running_loop().time()
        while True:
            lines = await conn.execute_write(bc.deal_poll_lua(target, mark))
            events = [ln[3:].split("|") for ln in lines if ln.startswith("EV|")]
            state = (_deal_field(lines, "STATE") or "nil|false|false|0").split("|")
            got = until(events)
            if got is not None or asyncio.get_running_loop().time() - t0 > timeout:
                return got, state
            await asyncio.sleep(0.25)

    def _answer_to(target, responding_to):
        """The AI's answer (its DealAction name) to our action, from its statements."""
        def find(events):
            for e in events:
                if e[0] == "S" and e[1] == str(target) and e[4] == responding_to:
                    return e[3]
            return None
        return find

    def _enacted_with(target):
        return lambda events: True if any(e[0] == "E" and str(target) in (e[1], e[2]) for e in events) else None

    async def _deal_finish(conn, target):
        """Close our deal session, then make sure the civ holds no deal toward the player: an offer it opened a
        session for is refused the way respond_to_trade refuses one. Returns a note for the agent when one is left
        that cannot be answered (its next turn would wait on it)."""
        await conn.execute_write(bc.deal_close_lua(target))
        await asyncio.sleep(0.5)
        _, state = await _deal_wait(conn, target, 10**9, lambda ev: None, timeout=0)
        if state[2] == "true" and state[0] not in ("nil", "-1"):
            await conn.execute_write(_lq.build_respond_to_deal(target, False))
            await asyncio.sleep(0.5)
            _, state = await _deal_wait(conn, target, 10**9, lambda ev: None, timeout=0)
        if state[2] == "true":
            _dlog.warning("Player %s still holds a deal toward the player after the trade (session %s)", target, state[0])
            return ("\nWarning: this civ still holds a deal toward you that the game will not show, which can stall "
                    "the AI turns; end_turn reloads the turn if they hang.")
        # Nothing is pending: empty the working deals, or the next statement this civ makes shows them as its offer.
        await conn.execute_write(bc.deal_clear_lua(target))
        return ""

    async def _test_trade_waits(self, other_player_id, offer_items, request_items):
        lua = _lq.build_test_trade(other_player_id, offer_items, request_items)
        lines = await self.conn.execute_write(bc.mark_test_trade(lua))
        mark = _deal_field(lines, "MARK")
        if mark is None:  # stopped early (not met, at war): nothing was sent
            return narrate_test_trade(_lq.parse_test_trade_response(lines))
        answer, _ = await _deal_wait(self.conn, other_player_id, int(mark), _answer_to(other_player_id, "EQUALIZE"))
        if answer in ("ADJUSTED", "PROPOSED", "ACCEPTED"):  # its counter-offer is the incoming deal now
            result = _lq.parse_test_trade_response(await self.conn.execute_write(bc.reread_test_trade(lua)))
        else:
            result = _lq.parse_test_trade_response(lines)
            result.counter, result.rejected = [], True
        out = narrate_test_trade(result)
        if answer is None:
            _dlog.warning("No answer from player %s to a trade test", other_player_id)
            out = out.replace("AI response: REJECTED", "AI response: NO ANSWER within "
                              f"{_DEAL_ANSWER_S:.0f} s, treat it as a refusal for now")
        elif _TEST_ACCEPTABLE in out:
            # Our terms came back unchanged, which says nothing (bench_compat.inspect_test_trade): ask the AI's check.
            lines = await self.conn.execute_write(bc.inspect_test_trade(lua))
            mark, verdict = _deal_field(lines, "MARK"), None
            if mark is not None:
                verdict, _ = await _deal_wait(self.conn, other_player_id, int(mark),
                                              _answer_to(other_player_id, "INSPECT"))
            if verdict == "REJECTED":
                out = out.replace(_TEST_ACCEPTABLE, (
                    "AI response: NOT ACCEPTABLE as-is: the AI made no counter-offer, and its check of these terms says "
                    "no, so a proposal may be refused. Ask for less or offer more and test again; terms it calls "
                    "ACCEPTABLE go through when sent"))
            elif verdict != "ACCEPTED":
                _dlog.warning("No answer from player %s to the check of a trade test (%s)", other_player_id, verdict)
                out = out.replace(_TEST_ACCEPTABLE, (
                    f"AI response: NO ANSWER to its check of these terms within {_DEAL_ANSWER_S:.0f} s (it made no "
                    "counter-offer), treat it as a refusal for now"))
        return out + await _deal_finish(self.conn, other_player_id)

    async def _propose_trade_waits(self, other_player_id, offer_items, request_items):
        conn, target = self.conn, other_player_id
        _, state = await _deal_wait(conn, target, 10**9, lambda ev: None, timeout=0)
        if state[2] == "true" and state[0] not in ("nil", "-1") and state[3] != "0":
            return ("Error: OFFER_PENDING|This civ has an offer waiting for your answer. Read it with "
                    "get_pending_trades and answer it with respond_to_trade before you propose a deal.")
        await conn.execute_write(bc.deal_close_lua(target))
        items = " ".join([_lua_deal_item("me", i) for i in offer_items] + [_lua_deal_item("target", i) for i in request_items])
        lines = await conn.execute_write(bc.deal_propose_lua(target, items))
        err = next((ln for ln in lines if ln.startswith("ERR:")), None)
        if err:
            return "Error: " + err[4:]
        name, mark, terms = _deal_field(lines, "CIV") or f"player {target}", int(_deal_field(lines, "MARK")), \
            _deal_field(lines, "TERMS")
        answer, _ = await _deal_wait(conn, target, mark, _answer_to(target, "PROPOSED"))
        counter = None
        if answer in ("ADJUSTED", "PROPOSED"):  # its version of the deal; the same terms are ours to accept
            lines = await conn.execute_write(bc.deal_accept_lua(target, only_if_equal=True))
            counter = _deal_field(lines, "NOT_EQUAL")
            if counter is None and _deal_field(lines, "MARK") is not None:
                answer, mark = "ACCEPTED", int(_deal_field(lines, "MARK"))
        if answer == "ACCEPTED":  # the game enacts the deal with the AI's acceptance; the player sends nothing more
            enacted, _ = await _deal_wait(conn, target, mark, _enacted_with(target))
            result = (f"ACCEPTED|{name} accepted, and the deal is in effect: {terms}." if enacted else
                      f"UNCLEAR|{name} accepted ({terms}), but the game did not confirm the deal. Check "
                      f"get_empire_resources and your gold before you propose it again.")
            return result + await _deal_finish(conn, target)
        if counter is not None:
            result = (f"COUNTER|{name} did not accept these terms; nothing was traded. It would accept: {counter}. "
                      f"To take that, propose those terms.")
        elif answer is None:
            result = f"NO_ANSWER|{name} did not answer within {_DEAL_ANSWER_S:.0f} s; nothing was traded."
        else:
            result = f"REJECTED|{name} rejected the deal; nothing was traded."
        return result + await _deal_finish(conn, target)

    async def _respond_to_deal_waits(self, other_player_id, accept):
        if not accept:
            lines = await self.conn.execute_write(_lq.build_respond_to_deal(other_player_id, False))
            return _gsm._action_result(lines) + await _deal_finish(self.conn, other_player_id)
        lines = await self.conn.execute_write(bc.deal_accept_lua(other_player_id))
        err = next((ln for ln in lines if ln.startswith("ERR:")), None)
        if err:
            return "Error: " + err[4:]
        mark = int(_deal_field(lines, "MARK"))
        enacted, _ = await _deal_wait(self.conn, other_player_id, mark, _enacted_with(other_player_id))
        note = await _deal_finish(self.conn, other_player_id)
        terms = _deal_field(lines, "TERMS")
        if enacted:
            return f"DEAL_ACCEPTED|The deal is in effect: {terms}." + note
        if getattr(self, "_pending_end_turn", False):
            # The AI turns are paused for this answer, and the game enacts the deal when they go on (game 13's turn
            # 108, replayed live twice: DiplomacyDealEnacted came then, and Rome was allied on turn 109).
            return (f"DEAL_ACCEPTED|Accepted: {terms}. The AI turns paused for your answer; the game puts the deal in "
                    f"effect when they go on (end_turn)." + note)
        return f"DEAL_UNCLEAR|Accepted ({terms}), but the game did not confirm the deal." + note

    _gsm.GameState.test_trade = _test_trade_waits
    _gsm.GameState.propose_trade = _propose_trade_waits
    _gsm.GameState.respond_to_deal = _respond_to_deal_waits

    for _name in ("respond_to_diplomacy", "respond_to_trade", "propose_trade", "test_trade", "send_diplomatic_action",
                  "propose_peace", "form_alliance"):
        _tool = mcp._tool_manager.get_tool(_name)
        if _tool is not None:
            _tool.fn = _then_close_leader_screen(_tool.fn)

    # A melee attack from 2 or more tiles away is a move-and-attack. civ6-mcp sends the order and reads the unit's
    # position in the same Lua call, before the order has run, so it always found the unit on its starting tile and
    # answered "STOPPED_SHORT ... Try again next turn from closer position" (12 to 26 times a game). In games 3, 7
    # and 8 the next unit listing showed the unit had moved every time, and it had usually attacked: the target's HP
    # had dropped, or it was dead and the unit stood on its tile. Here the unit and the target tile are read again
    # until the order has played out (about 2 seconds, at most 6), and the result says what happened.
    def _attack_state_lua(unit_index, tx, ty):
        return (
            "local me = Game.GetLocalPlayer() "
            f"local u = UnitManager.GetUnit(me, {int(unit_index)}) "
            "if u == nil or u:GetX() == -9999 then print('ME|GONE') else "
            f"  print('ME|' .. u:GetX() .. '|' .. u:GetY() .. '|' .. Map.GetPlotDistance(u:GetX(), u:GetY(), {int(tx)}, "
            f"{int(ty)}) .. '|' .. (u:GetMaxDamage() - u:GetDamage()) .. '|' .. u:GetMovesRemaining()) "
            "end "
            f"local us = Map.GetUnitsAt({int(tx)}, {int(ty)}) local any = false "
            "if us then for o in us:Units() do if o:GetOwner() ~= me then "
            "  local e = GameInfo.Units[o:GetType()] any = true "
            "  print('FOE|' .. (e and e.UnitType or '?') .. '|' .. (o:GetMaxDamage() - o:GetDamage()) .. '|' "
            "    .. (e and e.Combat or 0)) "
            "end end end "
            # no unit: an enemy city centre or Encampment (bench_compat.attack_lua), its hit points, strength -1
            f"local pl = Map.GetPlot({int(tx)}, {int(ty)}) local ow = pl and pl:GetOwner() or -1 "
            "if not any and ow >= 0 and ow ~= me and Players[ow] and pl:GetDistrictType() >= 0 then "
            "  for _, d in Players[ow]:GetDistricts():Members() do "
            f"    if d:GetX() == {int(tx)} and d:GetY() == {int(ty)} then "
            "      local function hp(k) local a, m = pcall(function() return d:GetMaxDamage(k) end) "
            "        local b, g = pcall(function() return d:GetDamage(k) end) return ((a and m) or 0) - ((b and g) or 0) end "
            "      local ok, gm = pcall(function() return d:GetMaxDamage(DefenseTypes.DISTRICT_GARRISON) end) "
            "      if ok and gm and gm > 0 then "
            f"        local c = Cities.GetPlotPurchaseCity({int(tx)}, {int(ty)}) "
            "        print('FOE|' .. GameInfo.Districts[d:GetType()].DistrictType .. (c and (' of ' .. "
            "          Locale.Lookup(c:GetName())) or '') .. '|' .. (hp(DefenseTypes.DISTRICT_GARRISON) "
            "          + hp(DefenseTypes.DISTRICT_OUTER)) .. '|-1') "
            "      end "
            "    end "
            "  end "
            "end "
            "print('---END---')"
        )

    async def _attack_state(game, unit_index, tx, ty):
        """(me, foe): me is 'gone' or (x, y, distance to target, HP, moves left); foe is (unit type, HP, combat
        strength) of the unit an attack on the tile hits (a military one before a civilian), or None. None when the
        read fails."""
        try:
            lines = await game.conn.execute_write(_attack_state_lua(unit_index, tx, ty), timeout=10.0)
        except Exception:
            return None
        me, foes = None, []
        for ln in lines:
            p = ln.split("|")
            if p[0] == "ME":
                me = "gone" if p[1] == "GONE" else tuple(int(float(v)) for v in p[1:6])
            elif p[0] == "FOE" and len(p) >= 4:
                foes.append((p[1], int(float(p[2])), int(float(p[3]))))
        if me is None:
            return None
        foe = next((f for f in foes if f[2] > 0), foes[0] if foes else None)
        return me, foe

    def _attack_resolved(before, after) -> bool:
        (bme, bfoe), (ame, afoe) = before, after
        if ame == "gone" or ame[2] == 0:  # died, or killed the target and moved onto its tile
            return True
        if bfoe and (afoe is None or afoe[0] != bfoe[0] or afoe[1] != bfoe[1]):
            return True
        return ame[3] != bme[3]

    def _attack_report(before, after, tx, ty, waited) -> str:
        (bme, bfoe), (ame, afoe) = before, after
        foe = bfoe[0] if bfoe else "the target"
        start = f"({bme[0]},{bme[1]})"
        if ame == "gone":
            return (f"MELEE_ATTACK|target:{foe} at ({tx},{ty})|Your unit moved from {start} to attack and no longer "
                    "exists: it died in the attack.")
        here = f"({ame[0]},{ame[1]})"
        moves = f"moves left: {ame[4]}"
        if _attack_resolved(before, after):
            killed = bfoe and (afoe is None or afoe[0] != bfoe[0])
            gone = "killed" if bfoe and bfoe[2] > 0 else ("taken" if bfoe and bfoe[2] < 0 else "captured")
            enemy = f"enemy HP:{bfoe[1]} -> {gone}" if killed else (f"enemy HP:{bfoe[1]} -> {afoe[1]}" if bfoe else "")
            where = f"advanced into ({tx},{ty})" if ame[2] == 0 else f"attacked from {here}"
            rule = ("\n  A city falls to a melee unit's attack once its hit points are at 0 (walls take the damage "
                    "first); ranged units cannot take it." if bfoe and bfoe[2] < 0 and not killed else "")
            return (f"MELEE_ATTACK|target:{foe} at ({tx},{ty})|moved from {start} and {where}|{enemy}"
                    f"|your HP:{bme[3]} -> {ame[3]}|{moves}" + rule)
        if (ame[0], ame[1]) == (bme[0], bme[1]):
            return (f"Error: NOT_MOVED|The move-and-attack order was sent, but after {waited:.0f} seconds the unit is "
                    f"still at {start} and no combat has happened. Check get_units before you order it again.")
        if ame[2] == 1:  # the game stops a move-and-attack next to the target when the unit cannot go on
            then = (f"The game stopped it there with {ame[4]} moves left, " + bc.SHORT_OF_MOVES if ame[4] > 0
                    else "It has no moves left to attack this turn.")
            return (f"MOVED_ADJACENT|Unit moved from {start} to {here}, next to {foe} at ({tx},{ty}), and did not "
                    f"attack ({moves}). {then}")
        return (f"Error: STOPPED_SHORT|Unit moved from {start} to {here} but could not reach {foe} at ({tx},{ty}): "
                f"{ame[2]} tiles away, {moves}. No attack happened.")

    # When the game refused a ranged unit's shot at an adjacent target, civ6-mcp fell back to a melee move-and-attack.
    # Ranged units cannot melee, so that only moved the unit, often out of the city it garrisoned (14 times in games
    # 1-9, 11 of them from a city tile; "first call moved archer instead of ranged attack", game 8 turn 29). The
    # refusal's cause is unknown: the same units fired on the next call, and 162 other adjacent shots worked. Here a
    # ranged unit always takes the ranged path, a refused adjacent shot is tried once more a second later, and if the
    # game still refuses, the unit stays where it is and the agent is told. civ6-mcp's combat estimate also counted an
    # adjacent shot as melee (melee strength, river and flanking modifiers, damage to the attacker), so the estimate
    # treats every attack by a ranged unit as ranged.
    _RANGED_UNIT = '(unitInfo ~= nil and (unitInfo.RangedCombat or 0) > 0 and unitInfo.Domain ~= "DOMAIN_AIR")'
    _IS_RANGED = "local isRanged = UnitManager.CanStartOperation(unit, UnitOperationTypes.RANGE_ATTACK, nil, true)\n"
    _MELEE_FALLBACK = ("    elseif dist <= 1 then\n"
                       "        -- Ranged failed at melee range: fall through to melee attack below\n"
                       "        isRanged = false\n")
    _original_build_attack_unit = _lq.build_attack_unit

    def _build_attack_unit_ranged(unit_index, target_x, target_y):
        lua = _original_build_attack_unit(unit_index, target_x, target_y)
        if lua.count(_IS_RANGED) != 1 or lua.count(_MELEE_FALLBACK) != 1:
            logging.getLogger("civ_mcp_http").warning("civ6-mcp's attack Lua changed: ranged-attack fix not applied")
            return lua
        refused = (f"    elseif dist <= 1 then\n"
                   f'        print("ERR:RANGED_REFUSED|The game would not let " .. (unitInfo and unitInfo.UnitType or '
                   f'"the unit") .. " fire from (" .. ux .. "," .. uy .. ") at " .. enemyName .. " on ({int(target_x)},'
                   f'{int(target_y)}) next to it. The unit has not moved: ranged units cannot melee, so fire from '
                   f'another tile in range, or attack with another unit.")\n'
                   f'        print("{_lq.SENTINEL}"); return\n')
        lua = lua.replace(_IS_RANGED, _IS_RANGED.rstrip("\n") + f" or {_RANGED_UNIT}\n")
        return lua.replace(_MELEE_FALLBACK,
                           _MELEE_FALLBACK.replace("dist <= 1 then", f"dist <= 1 and not {_RANGED_UNIT} then") + refused)

    _lq.build_attack_unit = _build_attack_unit_ranged
    _original_estimate_query = _lq.build_combat_estimate_query

    def _estimate_query_ranged(unit_index, target_x, target_y):
        lua = _original_estimate_query(unit_index, target_x, target_y)
        if lua.count("local isRanged = attRS > 0 and dist > 1\n") != 1:
            logging.getLogger("civ_mcp_http").warning("civ6-mcp's estimate Lua changed: ranged fix not applied")
            return lua
        return lua.replace("local isRanged = attRS > 0 and dist > 1\n", "local isRanged = attRS > 0\n")

    _lq.build_combat_estimate_query = _estimate_query_ranged

    # Promotions broke the game's rule. civ6-mcp applies them with GameCore's SetPromotion (the game's own PROMOTE
    # command failed silently for its authors) and then healed the unit to full and left its moves. In the game, a
    # promotion heals EXPERIENCE_PROMOTE_HEALED HP (50 in the base game's GlobalParameters.xml) and ends the unit's
    # turn. Agents noticed ("Promotion did not consume the archer's attack", game 7 turn 82; "Promotion did not consume
    # War-Cart's moves and healed it fully - promote before attacking when possible", game 9 turn 27). Here the heal
    # and the end of the unit's turn follow the game's rule.
    _FULL_HEAL = "pcall(function() unit:SetDamage(0) end)\n"
    _PROMOTE_RULE = (
        "local healed = 50\n"
        "pcall(function() local p = GameInfo.GlobalParameters['EXPERIENCE_PROMOTE_HEALED'] "
        "if p then healed = tonumber(p.Value) or 50 end end)\n"
        "pcall(function() unit:SetDamage(math.max(0, unit:GetDamage() - healed)) end)\n"
        "pcall(function() UnitManager.FinishMoves(unit) end)\n")
    _PROMOTED_LINE = 'print("OK:PROMOTED|" .. promoName .. "|stored:" .. stored .. "->" .. storedAfter)\n'
    _original_build_promote_unit = _lq.build_promote_unit

    def _build_promote_unit_rule(unit_index, promotion_type):
        lua = _original_build_promote_unit(unit_index, promotion_type)
        if lua.count(_FULL_HEAL) != 1 or lua.count(_PROMOTED_LINE) != 1:
            logging.getLogger("civ_mcp_http").warning("civ6-mcp's promotion Lua changed: promotion rule not applied")
            return lua
        return lua.replace(_FULL_HEAL, _PROMOTE_RULE).replace(
            _PROMOTED_LINE, _PROMOTED_LINE[:-2] + ' .. "|healed up to " .. healed .. " HP, and the unit\'s turn has '
            'ended (the game\'s rule for promotions)")\n')

    _lq.build_promote_unit = _build_promote_unit_rule

    # A city's ranged attack on a target it cannot see crashed instead of saying so: civ6-mcp's NO_LOS message is
    # outside its f-string, so the Lua reads `"..." .. {target_x} .. ","`, a table, and fails with "operator .. is not
    # supported for table .. string" (game 7, turn 113; the agent blamed stacked units).
    _CITY_NO_LOS = '" .. {target_x} .. "," .. {target_y} .. "'
    _original_build_city_attack = _lq.build_city_attack

    def _build_city_attack_fixed(city_id, target_x, target_y):
        lua = _original_build_city_attack(city_id, target_x, target_y)
        return lua.replace(_CITY_NO_LOS, f"{int(target_x)},{int(target_y)}")

    _lq.build_city_attack = _build_city_attack_fixed

    # Hidden resources leaked. A strategic resource stays hidden until its tech (Resources.PrereqTech: Niter needs
    # Military Engineering, Iron Bronze Working, ...), and civ6-mcp's map tools hide it until then, but get_cities
    # ("Needs builder: NITER@x,y", in every briefing), get_builder_tasks (game 9, turn 29: a Niter mine listed as
    # URGENT before it was revealed) and the wonder advisor named it. Here those three read resources through the
    # same check the map tools use.
    _RES_SEEN_LUA = (
        "local function __benchRes(plot) "
        "  local idx = plot:GetResourceType() "
        "  if idx < 0 then return idx end "
        "  local r = GameInfo.Resources[idx] "
        "  if r == nil or r.PrereqTech == nil then return idx end "
        "  local t = GameInfo.Technologies[r.PrereqTech] "
        "  if t == nil or Players[Game.GetLocalPlayer()]:GetTechs():HasTech(t.Index) then return idx end "
        "  return -1 "
        "end\n")

    def _hides_unrevealed(name):
        original = getattr(_lq, name)

        @functools.wraps(original)
        def build(*args, **kwargs):
            lua = original(*args, **kwargs)
            if "plot:GetResourceType()" not in lua:
                logging.getLogger("civ_mcp_http").warning("civ6-mcp's %s changed: resource check not applied", name)
                return lua
            return _RES_SEEN_LUA + lua.replace("plot:GetResourceType()", "__benchRes(plot)")

        setattr(_lq, name, build)

    for _name in ("build_cities_query", "build_builder_tasks_query", "build_wonder_advisor_query"):
        _hides_unrevealed(_name)

    # get_gp_advisor failed every time (7 of 7 calls in games 3, 6 and 7: "Could not get GP advisor info. Is this a
    # Great Person unit?"). It reads the class from Units.GreatPersonClass, a column the game does not have; the
    # GreatPersonClasses table maps each class to its UnitType.
    _GP_CLASS = "pcall(function() gpClass = uInfo.GreatPersonClass end)\n"
    _original_gp_advisor = _lq.build_gp_advisor_query

    def _gp_advisor_class(unit_index):
        lua = _original_gp_advisor(unit_index)
        if lua.count(_GP_CLASS) != 1:
            logging.getLogger("civ_mcp_http").warning("civ6-mcp's GP advisor Lua changed: class lookup not fixed")
            return lua
        return lua.replace(_GP_CLASS, _GP_CLASS + (
            'if gpClass == nil or gpClass == "" then gpClass = "" '
            "for row in GameInfo.GreatPersonClasses() do "
            "if row.UnitType == uInfo.UnitType then gpClass = row.GreatPersonClassType break end end end\n"))

    _lq.build_gp_advisor_query = _gp_advisor_class

    # An attack on a city with no unit in it (bench_compat.attack_lua has why): the attack Lua takes the city centre or
    # Encampment as the target, and the report says what the district shows afterwards instead of civ6-mcp's "killed".
    # It sits under _attack_unit_settled, which retries and re-reads the attack.
    _lq.build_attack_unit = bc.attack_lua(_lq.build_attack_unit)  # GameState.attack_unit looks it up at call time
    _lq.build_make_trade_route = bc.trade_route_lua(_lq.build_make_trade_route)  # the refusal's reasons
    _lq.build_cities_query = bc.city_targets_lua(_lq.build_cities_query)  # the game's own attack targets
    _lq.build_send_envoy = bc.send_envoy_lua(_lq.build_send_envoy)  # says how many envoys are left
    for _name in ("build_settle_advisor_query", "build_global_settle_scan"):  # no sites on another civ's land
        setattr(_lq, _name, bc.settle_owned_lua(getattr(_lq, _name)))
    _vendor_send_envoy = _gsm.GameState.send_envoy

    async def _send_envoy_count(self, city_state_player_id):
        out = await _vendor_send_envoy(self, city_state_player_id)
        # civ6-mcp re-reads the count 0.1 s after the request, which may not have landed yet; the count the result
        # already gives (bench_compat.send_envoy_lua) is the one to keep.
        return re.sub(r" \(verified remaining: -?\d+\)$", "", out) if "to give" in out else out

    _gsm.GameState.send_envoy = _send_envoy_count
    _vendor_attack_unit = _gsm.GameState.attack_unit

    async def _attack_unit_districts(self, unit_index, target_x, target_y):
        out = await _vendor_attack_unit(self, unit_index, target_x, target_y)
        if "|target:DISTRICT_" not in out:
            return out
        await asyncio.sleep(0.5)
        try:
            lines = await self.conn.execute_write(bc.district_state_lua(target_x, target_y), timeout=10.0)
        except Exception:
            lines = []
        return bc.city_attack_report(out, next((ln for ln in lines if ln.startswith("DEF|")), ""))

    _original_attack_unit = _attack_unit_districts

    async def _attack_unit_settled(self, unit_index, target_x, target_y):
        before = await _attack_state(self, unit_index, target_x, target_y)
        result = await _original_attack_unit(self, unit_index, target_x, target_y)
        if "RANGED_REFUSED|" in result:
            await asyncio.sleep(1.0)
            result = await _original_attack_unit(self, unit_index, target_x, target_y)
            logging.getLogger("civ_mcp_http").info("Ranged attack refused once; the retry 1 s later gave: %s",
                                                   result.strip().splitlines()[-1][:160])
        if before is None or before[0] == "gone":
            return result
        estimated = bc.melee_estimated(result)  # an adjacent attack civ6-mcp could not see land (bench_compat)
        if "STOPPED_SHORT|" not in result and not estimated:
            return result
        after, waited = None, 0.0
        while waited < 6.0:
            await asyncio.sleep(0.5)
            waited += 0.5
            after = await _attack_state(self, unit_index, target_x, target_y) or after
            if after and _attack_resolved(before, after):
                break
        if after is None:
            return result
        if estimated:
            logging.getLogger("civ_mcp_http").info("Adjacent attack re-read after %.1f s: %s -> %s", waited, before,
                                                   after)
            if not _attack_resolved(before, after) and after[0][4] != before[0][4]:
                return result  # its moves are spent but no hit points changed yet: keep civ6-mcp's estimate
            i = _EST_START.search(result).start()
            return result[:i] + _adjacent_report(before, after, target_x, target_y, waited)
        logging.getLogger("civ_mcp_http").info("Move-and-attack re-read after %.1f s: %s -> %s", waited, before, after)
        return result.split("Error: STOPPED_SHORT|", 1)[0] + _attack_report(before, after, target_x, target_y, waited)

    _EST_START = re.compile(r"^MELEE_ATTACK\|", re.M)

    def _adjacent_report(before, after, tx, ty, waited) -> str:
        """What an attack from next to the target did, read back once it has played out."""
        (bme, bfoe), (ame, afoe) = before, after
        foe = bfoe[0] if bfoe else "the target"
        start = f"({bme[0]},{bme[1]})"
        if ame == "gone":
            return (f"MELEE_ATTACK|target:{foe} at ({tx},{ty})|Your unit attacked from {start} and no longer exists: "
                    "it died in the attack.")
        if _attack_resolved(before, after):
            report = _attack_report(before, after, tx, ty, waited)
            return report.replace(f"|moved from {start} and attacked from {start}|", f"|attacked from {start}|") \
                .replace(f"|moved from {start} and advanced into", "|advanced into")
        hp = f" still has {bfoe[1]} HP," if bfoe else " is untouched,"
        return (f"Error: NOT_ATTACKED|The game did not carry out the attack: after {waited:.0f} seconds {foe} at "
                f"({tx},{ty}){hp} and your unit at {start} still has its {bme[4]} moves left, "
                + bc.SHORT_OF_MOVES + " Check get_units before you order it again.")

    _gsm.GameState.attack_unit = _attack_unit_settled

    # set_city_production sends CityManager.RequestOperation and reads the queue straight back. While the game
    # holds orders (an exclusive popup is open: natural wonder, wonder built, era, or an AI diplomacy session
    # waits for an answer), the order waits in line and the read-back says SILENT_FAILURE, "Retry the same call".
    # Games 1-8 had 16 of these. In game 2, turn 224, the "failed" Moon Landing was in the queue once the agent
    # answered Germany's deal; in game 8, turn 179, the same orders worked right after dismiss_popup. Name the
    # session that holds the order, or close the popups and wait for it to land; send it once more only if it
    # still has not (the order clears the queue first, so a second copy cannot pile up).
    _original_set_production = _gsm.GameState.set_city_production

    async def _sessions_open(game) -> str | None:
        try:
            sessions = await game.get_diplomacy_sessions()
        except Exception:
            return None
        return ", ".join(f"{s.other_civ_name} ({s.other_leader_name})" for s in sessions) if sessions else None

    async def _production_now(game, city_id, item_name) -> str | None:
        try:
            lines = await game.conn.execute_read(_lq.build_verify_production(city_id, item_name))
        except Exception:
            return None
        return next((l.split("|", 1)[1] for l in lines if l.startswith("CONFIRMED|")), None)

    async def _set_production_settled(self, city_id, item_type, item_name, target_x=None, target_y=None):
        result = await _original_set_production(self, city_id, item_type, item_name, target_x, target_y)
        if not result.startswith("Error: SILENT_FAILURE|"):
            return result
        log = logging.getLogger("civ_mcp_http")
        held = await _sessions_open(self)
        if held:
            log.info("Production order %s held by a diplomacy session with %s", item_name, held)
            return (f"Error: ORDER_HELD|{item_name} is not set yet: a diplomacy session with {held} is open, and the "
                    "game holds city orders until you answer it (get_pending_diplomacy, then respond_to_diplomacy or "
                    "respond_to_trade). The order then goes through by itself; check the city before you set it again.")
        try:
            closed = await self.dismiss_popup()
        except Exception:
            closed = ""
        closed = ", ".join(dict.fromkeys(closed[len("Dismissed: "):].split(". ")[0].split(", "))) \
            if closed.startswith("Dismissed: ") else ""
        waited = 0.0
        while waited < 3.0:
            await asyncio.sleep(0.5)
            waited += 0.5
            turns = await _production_now(self, city_id, item_name)
            if turns:
                log.info("Production order %s landed %.1f s late (popups closed: %s)", item_name, waited, closed or "none")
                why = f"after open popups were closed ({closed})" if closed else f"{waited:.1f} s late"
                return f"PRODUCING|{item_name}|{turns} (the game applied the order {why})"
        retry = await _original_set_production(self, city_id, item_type, item_name, target_x, target_y)
        log.info("Production order %s still unset %.1f s later (popups closed: %s); sent again: %s",
                 item_name, waited, closed or "none", retry[:160])
        return retry

    _gsm.GameState.set_city_production = _set_production_settled

    # get_policies listed every unlocked policy the slots take, obsolete ones included; the game's own government
    # screen also checks IsPolicyObsolete. set_policies accepted an obsolete policy, the game took it out of its
    # slot again, and the next turn opened with an empty-slot blocker: game 3 slotted Conscription (replaced by
    # Levee en Masse) on 28 turns and Liberalism (New Deal) on 9, game 4 Conscription on 24 and Urban Planning
    # (Colonial Offices) on 9. Obsolete policies are no longer listed, and set_policies names what replaced one.
    _AVAIL_LOOP = "    if pCulture:IsPolicyUnlocked(policy.Index) then\n"
    _original_policies_query = _lq.build_policies_query
    _original_set_policies = _lq.build_set_policies

    def _policies_query_current():
        lua = _original_policies_query()
        if _AVAIL_LOOP not in lua:
            logging.getLogger("civ_mcp_http").warning("civ6-mcp's policies query changed: obsolete policies not hidden")
            return lua
        return lua.replace(_AVAIL_LOOP, (
            "    local obsOk, isObs = pcall(function() return pCulture:IsPolicyObsolete(policy.Hash) end)\n"
            "    if pCulture:IsPolicyUnlocked(policy.Index) and not (obsOk and isObs) then\n"))

    def _set_policies_current(assignments):
        lua = _original_set_policies(assignments)
        for slot, policy in assignments.items():
            anchor = f"local canSlot_{slot} = "
            if str(policy).upper() == "NONE" or anchor not in lua or not re.fullmatch(r"[A-Z0-9_]+", str(policy)):
                continue
            lua = lua.replace(anchor, (
                f"local obsOk_{slot}, obs_{slot} = pcall(function() return pCulture:IsPolicyObsolete(pe_{slot}.Hash) end); "
                f"if obsOk_{slot} and obs_{slot} then local by_{slot} = ''; "
                f"pcall(function() for r in GameInfo.ObsoletePolicies() do if r.PolicyType == '{policy}' then "
                f"local np = GameInfo.Policies[r.ObsoletePolicy]; "
                f"if np and pCulture:IsPolicyUnlocked(np.Index) then by_{slot} = r.ObsoletePolicy; break end end end end); "
                f"print('ERR:POLICY_OBSOLETE|{policy} is obsolete' .. (by_{slot} ~= '' and (': ' .. by_{slot} .. "
                f"' replaced it') or '') .. '. The game takes an obsolete policy out of its slot, so the slot would be "
                f"empty again next turn. Pick another policy from get_policies.'); print('{_lq.SENTINEL}'); return end; "
                + anchor), 1)
        return lua

    _lq.build_policies_query = _policies_query_current
    _lq.build_set_policies = _set_policies_current

    # skip_remaining_units, which agents call before nearly every end_turn, fortified and then ended the moves of
    # every unit with moves left. That also hit units with orders of their own: a scout on auto-explore (the game
    # moves it when the turn ends, so it sat still: 23 of 24 turns with a skip against 2 of 9 without), and a unit
    # still walking a move civ6-mcp had already called "STOPPED_MID_PATH" (it reads the tile while the unit moves):
    # 106 of 152 multi-turn moves followed by a skip had stopped by the next turn. The game's own test for "needs
    # orders" is unit:IsReadyToSelect() (GetFirstReadyUnit: "moves remaining, not automated"). Wait for the game to
    # finish moving units, then skip only the units that test says are waiting for orders.
    _UNIT_LOOP = "    if x ~= -9999 and unit:GetMovesRemaining() > 0 then\n"
    _KEEP_LUA = (
        "local me = Game.GetLocalPlayer() "
        "local busy = false pcall(function() busy = UI.IsGameCoreBusy() end) "
        "print('BUSY|' .. tostring(busy)) "
        "for _, unit in Players[me]:GetUnits():Members() do "
        "if unit:GetX() ~= -9999 and unit:GetMovesRemaining() > 0 then "
        "local ready, queued = true, false "
        "pcall(function() ready = unit:IsReadyToSelect() end) "
        "pcall(function() queued = UnitManager.GetQueuedDestination(unit) ~= nil end) "
        "if queued or not ready then print('KEEP|' .. unit:GetID()) end end end "
        f"print('{_lq.SENTINEL}')")

    async def _units_with_orders(game) -> set[int]:
        waited = 0.0
        while True:
            try:
                lines = await game.conn.execute_write(_KEEP_LUA)
            except Exception:
                return set()
            if "BUSY|true" not in lines or waited >= 4.0:
                return {int(l.split("|")[1]) for l in lines if l.startswith("KEEP|")}
            await asyncio.sleep(0.5)
            waited += 0.5

    def _sparing(lua, keep):
        if not keep:
            return lua
        if _UNIT_LOOP not in lua:
            logging.getLogger("civ_mcp_http").warning("civ6-mcp's skip/fortify Lua changed: units with orders not spared")
            return lua
        guard = "local __keep = {" + ", ".join(f"[{i}] = true" for i in sorted(keep)) + "}\n"
        return guard + lua.replace(
            _UNIT_LOOP, "    if x ~= -9999 and unit:GetMovesRemaining() > 0 and not __keep[unit:GetID()] then\n")

    async def _skip_remaining_ready(self):
        keep = await _units_with_orders(self)
        fortify_result = ""
        try:
            fortify_result = _gsm._action_result(
                await self.conn.execute_write(_sparing(_lq.build_fortify_remaining_units(), keep)))
        except Exception as e:
            logging.getLogger("civ_mcp_http").debug("Fortify remaining failed: %s", e)
        skip_result = _gsm._action_result(await self.conn.execute_read(_sparing(_lq.build_skip_remaining_units(), keep)))
        out = f"{fortify_result}\n{skip_result}" if fortify_result and not fortify_result.startswith("Error") \
            else skip_result
        if keep:
            logging.getLogger("civ_mcp_http").info("skip_remaining_units left %d units with orders alone", len(keep))
            out += (f"\nKEPT|{len(keep)} units the game does not count as waiting for orders (on auto-explore, still "
                    "moving, fortified or asleep) were left alone")
        return out

    _gsm.GameState.skip_remaining_units = _skip_remaining_ready

    # A move that reached its tile never said the unit had used up its moves, so agents sent the next order at once
    # and got "no moves remaining": 20 to 42 improve orders a game (games 1 to 8) came right after the builder's own
    # move, and a Great Scientist moved onto its Campus was refused with no reason and the tile listed as valid
    # (game 9, turn 67; it activated there the next turn). Both results now say so.
    def _moves_lua(unit_index):
        return (f"local u = Players[Game.GetLocalPlayer()]:GetUnits():FindID({unit_index}) "
                f"if u then print('MOVES|' .. tostring(u:GetMovesRemaining())) end print('{_lq.SENTINEL}')")

    async def _no_moves_left(game, unit_index) -> bool:
        try:
            lines = await game.conn.execute_read(_moves_lua(unit_index))
            return any(l.startswith("MOVES|") and float(l.split("|")[1]) <= 0 for l in lines)
        except Exception:
            return False

    _original_move_unit = _gsm.GameState.move_unit

    async def _move_says_moves_left(self, unit_index, target_x, target_y):
        result = await _original_move_unit(self, unit_index, target_x, target_y)
        head, sep, rest = result.partition("\n")
        if (f"now_at:{target_x},{target_y}|" in head + "|" and "|BLOCKED" not in head
                and await _no_moves_left(self, unit_index)):
            head += "|arrived with no moves left: it can build, found or activate there next turn"
        return head + sep + rest

    _gsm.GameState.move_unit = _move_says_moves_left

    _original_activate = _gsm.GameState.activate_great_person

    async def _activate_says_no_moves(self, unit_index):
        result = await _original_activate(self, unit_index)
        if result.startswith("Error: CANNOT_ACTIVATE|") and await _no_moves_left(self, unit_index):
            result += (" It has no moves left this turn, and a great person needs moves to activate: activate it "
                       "on the same tile next turn.")
        return result

    _gsm.GameState.activate_great_person = _activate_says_no_moves

    # When an exclusive popup is up, civ6-mcp's dismiss_popup (run before every end turn) calls Close() in each Lua
    # state named like a popup until it hides, up to 20 times. InvitePopup (multiplayer invites) never hides, so a
    # scan spent 20 round trips on it: 27 s against 5 s, in a third of the scans (57 of 170 in games 8 and 9), and
    # the agent read "InvitePopup" 20 times in the list of closed popups. The scan now skips it.
    import civ_mcp.game_lifecycle as _glc  # noqa: E402

    _original_dismiss = _glc.dismiss_popup
    _NEVER_HIDES = ("InvitePopup",)

    async def _dismiss_skipping(conn):
        states = getattr(conn, "lua_states", None)
        if not isinstance(states, dict):
            return await _original_dismiss(conn)
        skipped = {i: n for i, n in states.items() if n in _NEVER_HIDES}
        for i in skipped:
            states.pop(i, None)
        try:
            return await _original_dismiss(conn)
        finally:
            states.update(skipped)

    _glc.dismiss_popup = _dismiss_skipping

    # end_turn's turn report diffs two snapshots of the empire, and the snapshot read the units in GameCore, where
    # UnitManager.CanStartOperation does not exist. civ6-mcp's units query calls it to check line of sight when a
    # ranged unit has an enemy in range but not adjacent, so then the whole read failed ("[string]:65: function
    # expected instead of nil") and the report lost its events: units hurt or killed, buildings finished, cities
    # grown. All 309 "Post-turn snapshot failed" in the server log through game 10's turn 60 were this, about one turn
    # in six, often turns with fighting. get_units sends the same query to InGame, where it works; so does the
    # snapshot now (its overview and city reads already go there).
    _UNITS_QUERY = _lq.build_units_query()
    _original_execute_read = GameConnection.execute_read

    async def _units_read_in_game(self, lua_code, *args, **kwargs):
        if lua_code == _UNITS_QUERY:
            return await self.execute_write(lua_code, *args, **kwargs)
        return await _original_execute_read(self, lua_code, *args, **kwargs)

    GameConnection.execute_read = _units_read_in_game

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

    # The diplomacy-pause trap (games 1-7 lost 0 to 11 turns each, tools/turn_trap.py). An AI civ opens a proposal
    # while the AI civs move; civ6-mcp's end_turn stops with "Turn paused ... respond_to_diplomacy, then end_turn
    # again" and keeps its end-turn request in flight (_pending_end_turn). The answer lets the AI civs finish, so the
    # player's next turn starts. The next end_turn is meant to report that turn change, but civ6-mcp first checks
    # end-turn blockers, which now belong to the new turn ("empty queue in Nippur", units needing orders), and reports
    # them as if the old turn were still open. Agents then skipped every unit "to finish the old turn" and lost the
    # new one (game 6, turn 84). While a request is in flight there is nothing to unblock, so that first check is
    # skipped and civ6-mcp reports the turn change, with a line saying whether the new turn still needs playing.
    # Only the first query is skipped: civ6-mcp asks again when the turn fails to advance, and that answer counts.
    import contextvars  # noqa: E402

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
                if not await _request_dropped(game):
                    return await _pending_turn_report(fn, args, kwargs)  # in flight: civ6-mcp polls GameCore
                logging.getLogger("civ_mcp_http").info(
                    "The end-turn request from turn %s is no longer in flight (the turn is open again): sending a new "
                    "one", game._pending_end_turn_from)
                game._pending_end_turn = False
                game._pending_end_turn_from = None
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

    # The second hang, after first contact (game 8, turn 13, 11 hangs in a row; game 7, turn 20): Spain greeted the
    # player during the end of the turn, civ6-mcp reported "Turn paused" and kept its request in flight, but the
    # greeting had cancelled it and the turn was open again. Each later end_turn only waited ~10 minutes for a turn
    # change that nobody had asked for, and the reload brought back the same greeting. A request is in flight while
    # the player's turn is inactive. When the turn number is unchanged and the player's turn is active, the game is
    # waiting for the player, so the next end_turn sends a new request (game 7, turn 20: that one ended the turn in
    # 25 s). Checked twice, 3 s apart, so a request that is just resuming is not sent twice.
    async def _request_dropped(game) -> bool:
        start = getattr(game, "_pending_end_turn_from", None)
        if start is None:
            return False
        for i in range(2):
            if i:
                await asyncio.sleep(3)
            if await _turn_number(game) != start or await _turn_active(game) is not True:
                return False
        return True

    # A request dropped inside one end_turn. Game 19's turn 86 "hung" four times, 10 minutes each, and every time
    # civ6-mcp reloaded the turn and ended it again. Replayed from turn 85's save: civ6-mcp closed three wonder popups,
    # sent ACTION_ENDTURN, and 90 s later the player's turn was still active, with nothing blocking it
    # (NO_ENDTURN_BLOCKING, UI.CanEndTurn true) and no AI civ moving; civ6-mcp only polls the turn number, for 10
    # minutes. A second request then ended the turn at once. Here each request is watched: if 8 s later the turn number
    # is the one read before the request and the player's turn is still active (checked twice, 3 s apart), the request
    # is sent again when nothing blocks it, up to 3 times. While the AI civs move the player's turn is inactive, so the
    # watcher stops at its first check and sends nothing.
    _original_build_end_turn = _lq.build_end_turn
    _END_TURN_MARK = "local __bench_end_turn = true "
    _RESEND_LUA = (
        "local me = Game.GetLocalPlayer() local b = NotificationManager.GetFirstEndTurnBlocking(me) "
        "if UI.CanEndTurn() and b == EndTurnBlockingTypes.NO_ENDTURN_BLOCKING "
        "then UI.RequestAction(ActionTypes.ACTION_ENDTURN) print('RESENT') "
        "elseif b == EndTurnBlockingTypes.ENDTURN_BLOCKING_UNITS then print('BLOCKED|UNITS') "
        "else print('BLOCKED') end print('---END---')"
    )
    _lq.build_end_turn = lambda: _END_TURN_MARK + _original_build_end_turn()
    _original_conn_write = GameConnection.execute_write
    _WATCHERS: set = set()
    _REFUSAL = types.SimpleNamespace(event=None)

    def _refusal_event() -> asyncio.Event:
        """Set by the watcher when the game refused the end turn over a unit; see _EndTurnAsyncio."""
        if _REFUSAL.event is None:
            _REFUSAL.event = asyncio.Event()
        return _REFUSAL.event

    async def _resend_if_dropped(conn, start) -> int:
        game, sent = types.SimpleNamespace(conn=conn), 0
        for _ in range(3):
            await asyncio.sleep(8)
            for i in range(2):
                if i:
                    await asyncio.sleep(3)
                if await _turn_number(game) != start or await _turn_active(game) is not True:
                    return sent
            lines = await _original_conn_write(conn, _RESEND_LUA, timeout=10.0)
            if "BLOCKED|UNITS" in lines:
                logging.getLogger("civ_mcp_http").info("End turn: the game refused it, a unit needs orders (turn %s)",
                                                       start)
                _refusal_event().set()
            if "RESENT" not in lines:
                return sent
            sent += 1
            logging.getLogger("civ_mcp_http").warning(
                "End turn: the request did not take (turn %s still open, nothing blocking it): sent it again", start)
        return sent

    async def _write_watching_end_turn(self, lua_code, *args, **kwargs):
        if not (isinstance(lua_code, str) and lua_code.startswith(_END_TURN_MARK)):
            return await _original_conn_write(self, lua_code, *args, **kwargs)
        start = await _turn_number(types.SimpleNamespace(conn=self))  # before the request: the player's turn
        _refusal_event().clear()
        out = await _original_conn_write(self, lua_code, *args, **kwargs)
        if start is not None:
            task = asyncio.ensure_future(_resend_if_dropped(self, start))
            _WATCHERS.add(task)
            task.add_done_callback(_WATCHERS.discard)
        return out

    GameConnection.execute_write = _write_watching_end_turn

    # When the AI turns hang, civ6-mcp reloads the save made at the start of the turn and ends the turn again,
    # without telling the agent. Everything the agent did in that turn is gone (game 8, turn 209: the trades and the
    # research choice were undone and the agent did not know why research was empty again). Name it.
    from civ_mcp.game_state import GameState as _GameState  # noqa: E402

    _END_TURN_RESULTS = contextvars.ContextVar("bench_end_turn_results", default=None)
    _original_gs_end_turn = _GameState.end_turn

    # A diplomacy pause names the civ but not its player id, and respond_to_diplomacy needs the id: agents guessed
    # (Spain's greeting answered as player 1 in games 3, 7 and 8; Brazil's in game 9) and got a bare NO_SESSION.
    # The pause now carries the id, and NO_SESSION names the sessions that are open.
    _SESSION_LINES = ("diplomatic proposal from", "diplomacy encounter pending with")

    async def _with_player_ids(game, text):
        if not isinstance(text, str) or not any(m in text for m in _SESSION_LINES):
            return text
        try:
            sessions = await game.get_diplomacy_sessions()
        except Exception:
            return text
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if any(m in line for m in _SESSION_LINES):
                for s in sessions:
                    lines[i] = lines[i].replace(f"{s.other_civ_name} ({s.other_leader_name})",
                                                f"{s.other_civ_name} ({s.other_leader_name}, player {s.other_player_id})")
        return "\n".join(lines)

    _original_diplomacy_respond = _GameState.diplomacy_respond

    async def _respond_names_sessions(self, other_player_id, response):
        out = await _original_diplomacy_respond(self, other_player_id, response)
        if not (isinstance(out, str) and out.startswith("Error: NO_SESSION")):
            return out
        try:
            sessions = await self.get_diplomacy_sessions()
        except Exception:
            return out
        open_now = "; ".join(f"{s.other_civ_name} ({s.other_leader_name}), player {s.other_player_id}" for s in sessions)
        return (f"Error: NO_SESSION|No diplomacy session is open with player {other_player_id}. "
                + (f"Open now: {open_now}. Answer it with that player id." if open_now
                   else "None is open now, so nothing is waiting for an answer."))

    _GameState.diplomacy_respond = _respond_names_sessions

    async def _gs_end_turn_recorded(self, *args, **kwargs):
        out = await _with_player_ids(self, await _original_gs_end_turn(self, *args, **kwargs))
        seen = _END_TURN_RESULTS.get()
        if seen is not None and isinstance(out, str):
            seen.append(out)
        return out

    _GameState.end_turn = _gs_end_turn_recorded

    # A turn that ended was reported as "Turn 144 -> 144" (game 9, turn 144; 37 times in games 1-9, 27 of them in
    # game 4, which was at war most of the game). When a civ at war with the player opens a session during the AI
    # turns, civ6-mcp closes it, waits for the turn to change and goes on to the report, but keeps the turn number it
    # read before the session. The same number named the autosave, so the start of the new turn was saved over the
    # start of the old one (0_MCP_0144 held turn 145, and there was no 0_MCP_0145, the save a hang on turn 145 reloads),
    # and civ6-mcp's per-turn advisor budget was not reset. The autosave now takes the turn the game is on, and the
    # report the turn read after the end turn.
    import civ_mcp.end_turn as _etm  # noqa: E402

    _original_autosave = _etm.save_game

    async def _autosave_of_turn_on(conn, name, *args, **kwargs):
        m = re.fullmatch(r"0_MCP_(\d+)", name) if isinstance(name, str) else None
        if m:
            now = await _turn_number(types.SimpleNamespace(conn=conn))
            if now is not None and now > int(m[1]):
                logging.getLogger("civ_mcp_http").info("Autosave of turn %s named for it, not %s", now, name)
                name = f"0_MCP_{now:04d}"
        return await _original_autosave(conn, name, *args, **kwargs)

    _etm.save_game = _autosave_of_turn_on

    _original_execute_end_turn = _etm.execute_end_turn

    async def _end_turn_reports_turn_on(gs, *args, **kwargs):
        out = await _original_execute_end_turn(gs, *args, **kwargs)
        m = re.match(r"Turn (\d+) -> (\d+)", out) if isinstance(out, str) else None
        if not m or int(m[2]) > int(m[1]):
            return out
        now = await _turn_number(gs)
        if now is None or now <= int(m[1]):
            return out
        logging.getLogger("civ_mcp_http").info("Turn report said %s -> %s; the game is on turn %s", m[1], m[2], now)
        if now > getattr(gs, "_high_water_turn", 0):  # civ6-mcp's own bookkeeping for a turn that advanced
            gs._advisor_calls_this_turn = 0
            gs._high_water_turn = now
        return f"Turn {m[1]} -> {now}" + out[m.end():]

    _etm.execute_end_turn = _end_turn_reports_turn_on

    # A leader screen can also come up while end_turn is already waiting for the AI turns, after the checks around the
    # tools have run. Game 13's turn 108 hung twice that way (replayed live: Brazil was the only civ still in its turn,
    # no session or deal was open, and the screen was up; closing it let the turn finish within seconds). civ6-mcp
    # makes one InGame probe once the turn has been quiet for 45 s (it keeps InGame queries out of the AI turns
    # otherwise); the leader-screen check runs first there and closes a screen with no session behind it.
    _original_mid_turn_diplomacy = _etm._check_mid_turn_diplomacy

    async def _mid_turn_leader_screen_first(gs, lua, turn_before):
        _refusal_event().clear()
        try:
            lines = await gs.conn.execute_write(bc.LEADER_SCREEN_LUA, timeout=10.0)
        except Exception:
            lines = []
        if "LEADER_SCREEN|CLOSED" in lines:
            logging.getLogger("civ_mcp_http").warning(
                "End turn: closed a leader screen left open with no diplomacy session while the AI turns waited")
            for _ in range(10):
                await asyncio.sleep(2.0)
                now = await _etm._get_turn_number(gs)
                if now is not None and turn_before is not None and now > turn_before:
                    return None, True
        # The game refused the turn end because a unit needs orders. When a turn ends, the game first moves units
        # along their multi-turn orders, and a unit can come out of that with moves left and nothing to do (its path
        # blocked, or it arrived early). The units check before end_turn cannot see that yet, and civ6-mcp waited
        # its full 10 minutes for a turn change before it named the blocker: 15 times in game 13 (about 2.5 hours),
        # 6 in game 10, twice by game 14's turn 101. One more order or skip ended each of those turns.
        if await _turn_active(gs) is True:
            try:
                ulines = await gs.conn.execute_write(_UNITS_BLOCKING_LUA, timeout=10.0)
            except Exception:
                ulines = []
            units = [ln.split("|") for ln in ulines if ln.startswith("UNIT|")]
            if "UNITS_BLOCK" in ulines and units:
                logging.getLogger("civ_mcp_http").warning("End turn: refused by the game, a unit needs orders")
                listed = "\n".join(f"  {t} [id:{i}] at ({xy}), moves {m}" for _, i, t, xy, m in units)
                return ("The turn did not end: as it ended, the game moved units along their orders, and a unit was "
                        "left needing orders (the game's end-turn button reads \"Unit needs orders\"). Units with "
                        "moves left:\n" + listed + "\nGive each an order (move, attack, fortify, skip) with "
                        "unit_action, or call skip_remaining_units, then end_turn again. The turn has not ended.",
                        False)
        return await _original_mid_turn_diplomacy(gs, lua, turn_before)

    _etm._check_mid_turn_diplomacy = _mid_turn_leader_screen_first

    # civ6-mcp makes that probe only after its polls have waited 54 s, so a turn the game refused over a unit took
    # about 70 s to report: 8 times in game 20 (about 9 minutes), once in game 19. The watcher above sees the refusal
    # 11 s after the request (turn unchanged, the player's turn active, ENDTURN_BLOCKING_UNITS). end_turn.py's waits
    # between turn polls (its asyncio.sleep calls over 2 s) then end at once, so its polls run on to the probe, which
    # checks the units again and reports them. The probe clears the flag, and every new request clears it too.
    class _EndTurnAsyncio:
        def __getattr__(self, name):
            return getattr(asyncio, name)

        @staticmethod
        async def sleep(delay, result=None):
            if delay <= 2.0:
                return await asyncio.sleep(delay, result)
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(_refusal_event().wait(), timeout=delay)
            return result

    _etm.asyncio = _EndTurnAsyncio()

    _HANGS: dict[str, int] = {}  # turn -> hangs so far

    def _hang_note(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            token = _END_TURN_RESULTS.set([])
            try:
                out = await fn(*args, **kwargs)
                seen = _END_TURN_RESULTS.get()
            finally:
                _END_TURN_RESULTS.reset(token)
            hangs = [s for s in seen if s.startswith("HANG:")]
            if not hangs or not isinstance(out, str):
                return out
            turn = hangs[0].split(":")[1]
            if len(seen) == 1 and out.startswith("HANG:"):  # civ6-mcp could not reload (no save): nothing retried
                logging.getLogger("civ_mcp_http").warning("Turn %s hung and was not reloaded", turn)
                return (f"The AI turns hung after you ended turn {turn}, and the game could not be reloaded "
                        f"automatically. Use restart_and_load with the turn's save.\n\n" + out)
            logging.getLogger("civ_mcp_http").info("Told the agent that turn %s was reloaded after a hang", turn)
            retries = max(1, len(seen) - 1)  # every end turn after the first was a retry
            times = "once" if retries == 1 else f"{retries} times"
            note = (f"The AI turns hung after you ended turn {turn}, so the game was reloaded from the save made at "
                    f"the start of turn {turn} and the turn was ended again ({times}). Everything you did in turn "
                    f"{turn} was undone: unit orders, production and research choices, purchases, trades. ")
            if re.match(rf"Turn {turn} -> \d+", out):
                note += "The turn then ended without them, and this is its report."
            else:
                note += (f"The result of ending it again is below. While turn {turn} is open, give your orders "
                         f"again (get_turn_briefing shows the turn) before you call end_turn.")
            # Game 19's turn 86 hung four times from its own save, with other research and production each time,
            # about 45 minutes in all; it ended at once after the agent loaded turn 85's save and played turn 85
            # with a few other orders. From the second hang of a turn, say so.
            _HANGS[turn] = _HANGS.get(turn, 0) + len(hangs)
            if _HANGS[turn] >= 2 and turn.isdigit() and int(turn) > 1:
                note += (f" Turn {turn} has now hung {_HANGS[turn]} times. In an earlier game a turn that hung again "
                         "after its reload kept hanging from its own save, though the orders in it changed each "
                         "time, and got past at once when the save from the start of the turn before was loaded and "
                         "that turn was played with a few different orders. If this turn hangs again, do that: "
                         f"load_game_save(\"0_MCP_{int(turn) - 1:04d}\"), then play turn {int(turn) - 1} again.")
            return note + "\n\n" + out

        return wrapper

    # Auto-explore lasted one turn. unit_action's "automate" sends the game's own UNITOPERATION_AUTOMATE_EXPLORE (as
    # the game's unit panel does), and the scout explores that turn, but from the next turn on it sat on its tile with
    # full moves and needed orders again (game 8: turns 19-20 at (38,38), 24-25 at (37,34); game 9: "automation
    # appears to drop each turn - re-issuing automate every turn", then "moving scout manually from now on"). What
    # cancels it was not found. Here the harness remembers the units the agent automated and sends auto-explore again
    # at the start of each of its turns, until the agent gives that unit any other order or the unit stops moving.
    _EXPLORE_HASH = 'GameInfo.UnitOperations["UNITOPERATION_AUTOMATE_EXPLORE"].Hash'

    def _explore_again_lua(ids):
        return (
            f"local me = Game.GetLocalPlayer() local hash = {_EXPLORE_HASH} "
            f"for _, id in ipairs({{{', '.join(str(int(i)) for i in ids)}}}) do "
            "  local u = UnitManager.GetUnit(me, id % 65536) "
            "  if u == nil or u:GetX() == -9999 then print('EXPLORER|' .. id .. '|GONE') "
            "  else "
            "    local x, y, m = u:GetX(), u:GetY(), u:GetMovesRemaining() "
            "    local sent = 'KEPT' "
            "    if m > 0 and UnitManager.CanStartOperation(u, hash, nil, nil) then "
            "      UnitManager.RequestOperation(u, hash, {}) sent = 'SENT' "
            "    elseif m > 0 then sent = 'REFUSED' end "
            "    print('EXPLORER|' .. id .. '|' .. sent .. '|' .. x .. '|' .. y .. '|' .. m) "
            "  end "
            "end print('---END---')"
        )

    def _tracks_explorers(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            out = await fn(*args, **kwargs)
            try:
                ctx = kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)
                uid, action = kwargs.get("unit_id"), str(kwargs.get("action") or "").lower()
                game = srv._get_game(ctx) if ctx is not None else None
                if game is not None and uid is not None:
                    explorers = game.__dict__.setdefault("_bench_explorers", {})
                    m = re.match(r"AUTOMATED\|(\d+),(\d+)", str(out))
                    if action == "automate" and m:
                        explorers[int(uid)] = (int(m.group(1)), int(m.group(2)))
                    elif action != "automate":
                        explorers.pop(int(uid), None)
            except Exception:
                logging.getLogger("civ_mcp_http").warning("explorer tracking failed", exc_info=True)
            return out

        return wrapper

    async def _explore_again(game, reloaded=False) -> str:
        explorers = game.__dict__.get("_bench_explorers") or {}
        if not explorers or await _turn_active(game) is not True:
            return ""
        lines = await game.conn.execute_write(_explore_again_lua(sorted(explorers)), timeout=10.0)
        sent, stopped = [], []
        for ln in lines:
            p = ln.split("|")
            if p[0] != "EXPLORER" or len(p) < 3:
                continue
            uid = int(p[1])
            if p[2] == "GONE":
                explorers.pop(uid, None)
                continue
            x, y, moves = int(p[3]), int(p[4]), int(float(p[5]))
            # It did not move during the last turn (a hang reload puts it back, so that does not count), or the game
            # will not explore from here: auto-explore is over.
            if moves > 0 and ((explorers.get(uid) == (x, y) and not reloaded) or p[2] == "REFUSED"):
                explorers.pop(uid, None)
                stopped.append(f"unit {uid} at ({x},{y})")
                continue
            explorers[uid] = (x, y)
            if p[2] == "SENT":
                sent.append(f"unit {uid} from ({x},{y})")
        logging.getLogger("civ_mcp_http").info("Auto-explore sent again: %s; stopped: %s", sent, stopped)
        note = ""
        if sent:
            note += (f"\n\nAuto-explore continues for {', '.join(sent)} (the harness sends it again each turn "
                     "until you give the unit another order).")
        if stopped:
            note += (f"\n\nAuto-explore has stopped for {', '.join(stopped)}: it did not move last turn, or the game "
                     "will not explore from there. Give it orders.")
        return note

    def _explores_again(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            out = await fn(*args, **kwargs)
            if isinstance(out, str) and re.search(r"Turn \d+ -> \d+", out):
                ctx = kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)
                try:
                    out += await _explore_again(srv._get_game(ctx), reloaded=out.startswith("The AI turns hung"))
                except Exception:
                    logging.getLogger("civ_mcp_http").warning("sending auto-explore again failed", exc_info=True)
            return out

        return wrapper

    # end_turn's promotion blocker never said which unit ("* Unit available for promotion -> Use:
    # get_unit_promotions(unit_id=...)", 262 times in games 1-9; "A promotion notification is pending but I couldn't
    # tell which unit", game 7, turn 129). Name the units, by the XP formula civ6-mcp's own blocker check uses.
    _PROMO_LUA = (
        "local me = Game.GetLocalPlayer() "
        "for _, u in Players[me]:GetUnits():Members() do "
        "  if u:GetX() ~= -9999 then "
        "    local ok, exp = pcall(function() return u:GetExperience() end) "
        "    local ui = GameInfo.Units[u:GetType()] "
        "    local promClass = ui and ui.PromotionClass or '' "
        "    if ok and exp and promClass ~= '' then "
        "      local promoCount = 0 "
        "      for p in GameInfo.UnitPromotions() do "
        "        if p.PromotionClass == promClass and exp:HasPromotion(p.Index) then promoCount = promoCount + 1 end "
        "      end "
        "      local needed = exp:GetExperienceForNextLevel() * (promoCount + 1) * (promoCount + 2) / 2 "
        "      if exp:GetExperiencePoints() >= needed then "
        "        print('PROMO|' .. u:GetID() .. '|' .. ui.UnitType .. '|' .. u:GetX() .. ',' .. u:GetY()) "
        "      end "
        "    end "
        "  end "
        "end print('---END---')"
    )
    _PROMO_LINE = "* Unit available for promotion"

    def _names_promotions(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            out = await fn(*args, **kwargs)
            if not isinstance(out, str) or _PROMO_LINE not in out:
                return out
            try:
                ctx = kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)
                lines = await srv._get_game(ctx).conn.execute_read(_PROMO_LUA, timeout=10.0)
                units = ["{1} {0} at ({2})".format(*ln.split("|")[1:4]) for ln in lines if ln.startswith("PROMO|")
                         and len(ln.split("|")) >= 4]
                if units:
                    i = out.index(_PROMO_LINE) + len(_PROMO_LINE)
                    out = out[:i] + " (" + "; ".join(units) + ")" + out[i:]
            except Exception:
                logging.getLogger("civ_mcp_http").warning("naming promotable units failed", exc_info=True)
            return out

        return wrapper

    # A discovered spy (game 21, turns 132 and 156): civ6-mcp picks its escape route itself while the turn ends and
    # only logs the pick, so the agent saw a prompt it could not answer and then no spy. end_turn now says so
    # (bench_compat.escape_note).
    _ESCAPES: list[str] = []

    class _EscapeLog(logging.Filter):
        def filter(self, record):
            if isinstance(record.msg, str) and record.msg.startswith("Auto-resolved spy escape"):
                _ESCAPES.append(record.getMessage())
            return True

    logging.getLogger("civ_mcp.end_turn").addFilter(_EscapeLog())

    def _reports_escapes(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            _ESCAPES.clear()
            out = await fn(*args, **kwargs)
            note = bc.escape_note(_ESCAPES) if isinstance(out, str) else ""
            return out + "\n\n" + note if note else out

        return wrapper

    _tool = mcp._tool_manager.get_tool("end_turn")
    _tool.fn = _reports_escapes(_names_promotions(_explores_again(_hang_note(_units_first(_tool.fn)))))
    _tool = mcp._tool_manager.get_tool("unit_action")
    _tool.fn = _tracks_explorers(_tool.fn)

    # civ6-mcp's turn report calls every own unit missing after the turn "killed" ("Your Builder (UNIT_BUILDER) was
    # killed!"), including the ones the agent used up itself: a settler that founded a city, a builder's last charge,
    # an upgrade (the unit gets a new id), a disband. Those orders run asynchronously, so the unit is often still in
    # the snapshot taken when end_turn starts. That was 22 to 35 false alarms a game in games 6 to 8 ("'Builder
    # killed' messages are last-charge consumption; not enemy action", game 6, turn 107). Here the agent's own orders
    # that can use a unit up are remembered for the turn, and a unit that vanished after one is reported as such.
    _SPENDS = {"found_city": "was used to found a city", "improve": "used its last build charge",
               "remove_feature": "used its last build charge", "sacrifice_charges": "used up its charges",
               "delete": "was disbanded on your order", "activate": "was used up when activated",
               "spread_religion": "used its last spread charge", "upgrade": "was upgraded and has a new id"}
    _SPENT: dict[int, str] = {}

    def _records_spent(fn, action=None):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            out = await fn(*args, **kwargs)
            try:
                kind = action or str(kwargs.get("action") or "").lower()
                uid = kwargs.get("unit_id")
                if kind in _SPENDS and uid is not None and not str(out).lstrip().startswith("Error"):
                    _SPENT[int(uid)] = _SPENDS[kind]
            except Exception:
                logging.getLogger("civ_mcp_http").warning("recording a spent unit failed", exc_info=True)
            return out

        return wrapper

    _original_diff = _GameState.__dict__["_diff_snapshots"].__func__

    def _diff_with_spent(before, after):
        events = _original_diff(before, after)
        try:
            for uid, ub in before.units.items():
                reason = _SPENT.get(uid)
                if reason is None or uid in after.units:
                    continue
                if "build charge" in reason and getattr(ub, "build_charges", 0) > 1:
                    continue  # it had charges to spare (the snapshot may be one charge behind), so it was killed
                killed = f"Your {ub.name} ({ub.unit_type}) was killed! Last seen at ({ub.x},{ub.y})."
                for i, e in enumerate(events):
                    if e.message == killed:
                        events[i] = _lq.TurnEvent(priority=3, category=e.category, message=(
                            f"Your {ub.name} ({ub.unit_type}) {reason} (last seen at ({ub.x},{ub.y}))."))
                        break
            # A spy gets a new id when it travels, so the report called a spy that left a city "killed" (game 19:
            # Raheem on turn 197 and Uday on turn 203, both "last seen" in the agent's own Isin; the agent wrote that
            # Raheem had been killed arriving in Madrid, and later found him there). A spy listed again under its
            # name has moved; one not listed may be travelling or dead, and get_spies says which.
            for uid, ub in before.units.items():
                if ub.unit_type != "UNIT_SPY" or uid in after.units:
                    continue
                killed = f"Your {ub.name} ({ub.unit_type}) was killed! Last seen at ({ub.x},{ub.y})."
                now = next((u for u in after.units.values() if u.unit_type == "UNIT_SPY" and u.name == ub.name), None)
                if now is not None:
                    msg = (f"Your spy {ub.name} moved from ({ub.x},{ub.y}) to ({now.x},{now.y}) and has a new id, "
                           f"{now.unit_id}.")
                else:
                    msg = (f"Your spy {ub.name} is no longer listed among your units (last seen at ({ub.x},{ub.y})). "
                           "A spy gets a new id when it travels, so this alone does not mean it was killed: "
                           "get_spies lists the spies you have.")
                for i, e in enumerate(events):
                    if e.message == killed:
                        events[i] = _lq.TurnEvent(priority=2, category=e.category, message=msg)
                        break
        except Exception:
            logging.getLogger("civ_mcp_http").warning("rewording spent units failed", exc_info=True)
        _SPENT.clear()
        return events

    _GameState._diff_snapshots = staticmethod(_diff_with_spent)
    _tool = mcp._tool_manager.get_tool("unit_action")
    _tool.fn = _records_spent(_tool.fn)
    _tool = mcp._tool_manager.get_tool("upgrade_unit")
    if _tool is not None:
        _tool.fn = _records_spent(_tool.fn, action="upgrade")

    # unit_action had no pillage (bench_compat.PILLAGE_NOTE has why). pillage and pillage_route send the game's own
    # order on the unit's tile, then read the tile back once the order has played out.
    def _pillages(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            action = str(kwargs.get("action") or "").lower()
            if action not in bc.PILLAGE_OPS:
                return await fn(*args, **kwargs)
            ctx = kwargs.get("ctx") or next((a for a in args if isinstance(a, Context)), None)
            uid = int(kwargs["unit_id"])

            async def run():
                conn = srv._get_game(ctx).conn
                sent = _gsm._action_result(await conn.execute_write(bc.pillage_lua(uid % 65536, bc.PILLAGE_OPS[action]),
                                                                   timeout=10.0))
                if not sent.startswith("PILLAGE_SENT"):
                    return sent
                tile = ""
                for _ in range(6):  # the order runs a frame or more later
                    await asyncio.sleep(0.5)
                    tile = next((ln for ln in await conn.execute_write(bc.pillage_tile_lua(uid % 65536), timeout=10.0)
                                 if ln.startswith("TILE|")), "")
                    if "=pillaged" in tile:
                        break
                p = tile.split("|")
                if len(p) < 5:
                    return f"PILLAGE_SENT|{action} ordered; the unit's tile could not be read back."
                x, y, moves, items = p[1], p[2], p[3], p[4]
                return (f"PILLAGE_SENT|{action} at ({x},{y}). The tile now: {items.replace(',', ', ') or 'nothing to pillage'}"
                        f" (moves left: {moves}). If nothing reads pillaged, the order has not played out or did not take.")

            return await srv._logged(ctx, "unit_action", {"unit_id": uid, "action": action}, run)

        return wrapper

    _tool = mcp._tool_manager.get_tool("unit_action")
    _tool.fn = _pillages(_tool.fn)
    _tool.description += bc.PILLAGE_NOTE + bc.CITY_ATTACK_NOTE

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

# civ6-mcp loads a save from the menu by OCR: click "Single Player", then look 5 s for "Load Game". Sometimes the
# first click opens nothing, and OCR still reads the main menu (Single Player, Multiplayer, Game Options), so the
# load fails. In game 7 every reload failed this way for 30 minutes after the turn-102 hang, and game 8's start
# load failed once. Click "Single Player" again and look again, up to 3 times.
_original_click_text = launcher._click_text


def _click_text_again(target, *args, **kwargs):
    if _original_click_text(target, *args, **kwargs):
        return True
    if target != "Load Game":
        return False
    for i in range(3):
        logging.getLogger("civ_mcp_http").info("'Load Game' not found: clicking 'Single Player' again (%d/3)", i + 1)
        if _original_click_text("Single Player", timeout=10, exact=True, post_delay=1.5) and \
                _original_click_text(target, *args, **kwargs):
            return True
    return False


launcher._click_text = _click_text_again

# civ6-mcp brings the game to the front with SetForegroundWindow before each menu click, but Windows refuses that
# call from a background process, silently. OCR reads the game window's own pixels, so it still finds the buttons,
# while the clicks land on whatever window covers the game. On 2026-11-09 a browser window on the game's screen
# took every click: all of game 8's start loads failed. Raising the game in the z-order (topmost, then back to
# normal) needs no foreground rights, so the click reaches it.
_original_bring_to_front_win32 = launcher._bring_to_front_win32


def _bring_to_front_win32_raised() -> None:
    _original_bring_to_front_win32()
    import ctypes
    from ctypes import wintypes

    win = launcher._find_game_window_win32()
    if win is None:
        return
    u = ctypes.WinDLL("user32")  # its own function objects: civ6-mcp's ctypes.windll.user32 keeps its signatures
    u.GetForegroundWindow.restype = wintypes.HWND
    u.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                               ctypes.c_uint]
    hwnd = wintypes.HWND(win.window_id)
    if u.GetForegroundWindow() == hwnd.value:
        return
    flags = 0x0001 | 0x0002 | 0x0040  # SWP_NOSIZE | SWP_NOMOVE | SWP_SHOWWINDOW
    u.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, flags)  # HWND_TOPMOST
    u.SetWindowPos(hwnd, wintypes.HWND(-2), 0, 0, 0, 0, flags)  # HWND_NOTOPMOST: stays above the other windows
    logging.getLogger("civ_mcp_http").info("Game window was not in front: raised it above the other windows")


launcher._bring_to_front_win32 = _bring_to_front_win32_raised

# civ6-mcp clicks by moving the cursor onto the target and pressing. The game's menu only takes a click on a button
# it has seen the mouse move over, so once a click is lost the cursor stays on the button, and every later click
# there (the same spot after each relaunch) comes with no movement and is ignored. With the cursor moved off the
# button first, a menu load that had failed for 25 minutes worked on the first try (2026-11-09). Start each click
# 40 px away.
_original_click_win32 = launcher._click_win32


def _click_win32_moving(x: int, y: int) -> None:
    import ctypes
    import time

    u = ctypes.WinDLL("user32")
    old = None
    try:  # physical pixels, as civ6-mcp's own click uses
        u.SetThreadDpiAwarenessContext.restype = ctypes.c_ssize_t
        u.SetThreadDpiAwarenessContext.argtypes = [ctypes.c_ssize_t]
        old = u.SetThreadDpiAwarenessContext(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
    except Exception:
        pass
    u.SetCursorPos(int(x) + 40, int(y) + 40)
    if old:
        u.SetThreadDpiAwarenessContext(old)
    time.sleep(0.15)
    _original_click_win32(x, y)


launcher._click_win32 = _click_win32_moving

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
# uvicorn closes a keep-alive connection after 5 idle seconds by default. Claude Code's client sometimes sent the next
# call on a connection just as the server closed it, and the call failed with ECONNRESET without reaching the server:
# all 11 in games 10 to 12 (8 in game 12, one of them an end_turn) came 4.1 to 5.0 s after the previous result.
# With a long server timeout the client closes its idle connections first.
import uvicorn  # noqa: E402

_UvicornConfig = uvicorn.Config


class _LongKeepAliveConfig(_UvicornConfig):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("timeout_keep_alive", 3600)
        super().__init__(*args, **kwargs)


uvicorn.Config = _LongKeepAliveConfig
mcp.settings.host = "127.0.0.1"
mcp.settings.port = int(os.environ.get("CIV_MCP_PORT", "8771"))
mcp.run(transport="streamable-http")
