"""Base-game compatibility for civ6-mcp and its hotseat fork, which are written for Gathering Storm.

Shared by windows/civ_mcp_http.py (single player, FireTuner) and windows/civ_mcp_hotseat.py (hotseat, MCP Bridge).
- base_game_rewrite: each Lua chunk is rewritten to call CB_ names for expansion APIs, with base-game-compat.lua
  prepended (see that file). Tools that read favor, loyalty, eras or World Congress then get neutral values
  instead of failing.
- XP_TOOLS: the tools for systems the base game lacks (governors, dedications, World Congress), to remove.
- OUTPUT_RULES: lines in tool output that only make sense with the expansions.
- LEADER_SCREEN_LUA: closes a leader screen left open with no diplomacy session (it stalls the AI turns).
"""

import os
import re
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))

_CB_METHODS = (
    "GetFavor|GetGovernors|GetAllianceType|GetAllianceLevel|GetGrievancesAgainst|GetResourceStockpileCap|"
    "GetResourceAccumulationPerTurn|GetResourceImportPerTurn|GetUnitResourceDemandPerTurn|GetCulturalIdentity|"
    "GetDiplomaticVictoryPoints|GetScienceVictoryPoints|GetScienceVictoryPointsTotalNeeded|GetNextRebelledCity"
)
_XP_TABLES = (
    "Governors|GovernorPromotions|GovernorPromotionSets|GovernorPromotionPrereqs|CommemorationTypes|"
    "Resolutions|Alliances|GovernmentBonuses"
)
RULES = [
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
    # set_research / set_civic refuse anything already researched, but Future Tech and Future Civic repeat: once every
    # tech is done, the game asks for Future Tech again each turn and the turn could not end (game 2, turn 238).
    (re.compile(r"if Players\[id\]:(GetTechs|GetCulture)\(\):(HasTech|HasCivic)\(idx\) then"),
     lambda m: f"if Players[id]:{m[1]}():{m[2]}(idx) and not "
               f"GameInfo.{'Technologies' if m[2] == 'HasTech' else 'Civics'}[idx].Repeatable then"),
    # The game-over check names the victory with fallback tests. Game 4 won by Domination on turn 170 but was reported
    # as a Culture victory: the domination test reads PlayerCities:GetOriginalCapital(), which the base game lacks, so
    # it failed inside its pcall, and the culture test then counted 0 visiting tourists against 0 domestic ones as
    # culturally dominant. Domination: look for each rival's original capital among the winner's cities instead.
    (re.compile(r"local oCap = q:GetCities\(\):GetOriginalCapital\(\)\s+"
                r"if oCap and oCap:GetOwner\(\) == winnerId then owned = owned \+ 1 end"),
     "local held = false "
     "for _, c in wp:GetCities():Members() do "
     "if c:IsOriginalCapital() and c:GetOriginalOwner() == i then held = true end end "
     "if held then owned = owned + 1 end"),
    # Culture: no tourists at all is not dominance.
    (re.compile(r"if visit < stay then"), "if visit <= 0 or visit < stay then"),
    # Score is the last fallback, but a Score victory needs the turn limit. Right when a space race ends, the game
    # does not count the last project yet (game 5's first check said Score, one 39 s later Technology), so game 6's
    # Science win on turn 223 of 250 was reported as a Score victory. Before the turn limit, a winner one project
    # short of the space race won it.
    (re.compile(r'(\n\s*)victoryType = "VICTORY_SCORE"'),
     r'\1local svpL, needL, maxT = 0, 5, 0 '
     r'pcall(function() svpL = wp:GetStats():CB_GetScienceVictoryPoints() '
     r'needL = wp:GetStats():CB_GetScienceVictoryPointsTotalNeeded() end) '
     r'pcall(function() maxT = Game.GetMaxTurns() end) '
     r'if (maxT <= 0 or Game.GetCurrentGameTurn() < maxT) and svpL >= needL - 1 then '
     r'victoryType = "VICTORY_TECHNOLOGY" else victoryType = "VICTORY_SCORE" end'),
]

_OVERVIEW_RULES = [
    (re.compile(r" \| Favor: [^|\n]*"), ""),
    (re.compile(r"^(Era: [^|\n]+?) \| Score: .*$", re.M), r"\1"),
]
# civ6-mcp's list of spy missions (get_spies output, spy_action description) names two Rise and Fall missions and
# leaves out two the base game has (its UnitOperations data, checked on the game PC).
SPY_MISSION_LIST = re.compile(r"COUNTERSPY, GAIN_SOURCES, SIPHON_FUNDS, STEAL_TECH_BOOST,\s+SABOTAGE_PRODUCTION, "
                              r"GREAT_WORK_HEIST, RECRUIT_PARTISANS,\s+NEUTRALIZE_GOVERNOR, FABRICATE_SCANDAL")
SPY_MISSIONS = ("COUNTERSPY, GAIN_SOURCES, SIPHON_FUNDS, STEAL_TECH_BOOST, SABOTAGE_PRODUCTION, GREAT_WORK_HEIST, "
                "RECRUIT_PARTISANS, DISRUPT_ROCKETRY, LISTENING_POST")
OUTPUT_RULES = {
    "get_spies": [(SPY_MISSION_LIST, SPY_MISSIONS)],
    "get_game_overview": _OVERVIEW_RULES,
    "get_turn_briefing": _OVERVIEW_RULES,
    "begin_standin_turn": _OVERVIEW_RULES,
    "get_diplomacy": [
        (re.compile(r"Diplomatic Service civic\)"), "Civil Service civic)"),
    ],
    "get_victory_progress": [
        (re.compile(r"launch 4 space projects = 50 VP"), "5 space projects: Earth Satellite, Moon Landing, 3 Mars"),
    ],
}
XP_TOOLS = [
    "get_governors", "appoint_governor", "assign_governor", "promote_governor",
    "get_dedications", "choose_dedication", "get_world_congress", "queue_wc_votes",
]
ALLIANCE_NOTE = (
    "\n\nBase game: there is one alliance type (alliance_type is ignored), and it needs the Civil Service "
    "civic, not Diplomatic Service."
)

# Spy missions the base game has (Base/Assets/Gameplay/Data/UnitOperations.xml) but civ6-mcp leaves out of its op
# table, so get_spies never offered them and spy_action answered UNKNOWN_MISSION. Game 11, turn 172: the agent sent
# DISRUPT_ROCKETRY into a Greek city, got UNKNOWN_MISSION, wrote that Greece's space race could not be slowed, and
# Greece won it about 5 turns ahead. The game hashes an op as ~crc32 of its type name, which reproduces all ten
# hashes civ6-mcp hardcodes.
def op_hash(type_name: str) -> int:
    h = ~zlib.crc32(type_name.encode()) & 0xFFFFFFFF
    return h - (1 << 32) if h >= 1 << 31 else h


SPY_OPS = {name: op_hash("UNITOPERATION_SPY_" + name) for name in ("DISRUPT_ROCKETRY", "LISTENING_POST")}
SPY_NOTE = (
    "\n\nAlso in the base game: DISRUPT_ROCKETRY, against a city with a Spaceport district (8 turns; on success the "
    "city loses progress on its space race project), and LISTENING_POST. get_spies lists each where the spy can "
    "start it."
)

# Trades. The AI answers a deal a frame or more after it is sent, as a diplomacy statement in the open session (the
# game's DiplomacyDealView waits for it before it lets the player accept). civ6-mcp did each step in one Lua call:
# - test_trade sent EQUALIZE and closed the session at once. The AI's late answer then stayed behind as a deal of its
#   own, pending toward the player. With terms, it was a live offer the agent took for a test; empty (an AI that will
#   not trade), the leader screen closes its session on sight (MakeDeal_TestValid), so it can never be answered, and
#   that civ's next turn waits on it forever. Game 12's turn 96 hung that way on Rome; replayed from its autosave it
#   hung again, stuck on Rome's turn with only HasPendingDeal(Rome, player) set, and nothing cleared it afterwards.
# - propose_trade sent PROPOSED and ACCEPTED together, before any answer, and reported the incoming deal left from
#   the last test as the "actual terms". Agents saw ACCEPTED with nothing traded and REJECTED for deals that went
#   through (game 12, turn 120), and in the replay the same Marble deal was enacted twice.
# - respond_to_trade accepted without copying the AI's offer into the player's working deal, as the deal view does.
# The calls below keep the session open until the answer comes, read it from the statement events, accept only
# terms the AI accepted, and report the deal the game enacted.
DEAL_LISTENER = (
    "if not BENCH_DEALS then BENCH_DEALS = {n = 0} "
    "local function bdName(a) for k, v in pairs(DealProposalAction) do if v == a then return k end end return tostring(a) end "
    "Events.DiplomacyStatement.Add(function(f, t, kv) local d = BENCH_DEALS d.n = d.n + 1 "
    "d[d.n] = 'S|' .. tostring(f) .. '|' .. tostring(t) .. '|' .. bdName(kv.DealAction) .. '|' .. bdName(kv.RespondingToDealAction) end) "
    "Events.DiplomacyDealEnacted.Add(function(a, b) local d = BENCH_DEALS d.n = d.n + 1 "
    "d[d.n] = 'E|' .. tostring(a) .. '|' .. tostring(b) end) "
    "end "
)
DEAL_TERMS_FN = (
    "local function benchTerms(d, me) local give, get = {}, {} "
    "if d then for it in d:Items() do "
    "local ty, amt, dur = it:GetType(), it:GetAmount() or 0, it:GetDuration() or 0 local s = 'an item' "
    "if ty == DealItemTypes.GOLD then s = dur > 0 and (amt .. ' gold/turn (' .. dur .. ' turns)') or (amt .. ' gold') "
    "elseif ty == DealItemTypes.RESOURCES then local r = GameInfo.Resources[it:GetValueType()] "
    "s = (r and Locale.Lookup(r.Name) or 'a resource') .. (dur > 0 and (' (' .. dur .. ' turns)') or '') "
    "elseif ty == DealItemTypes.AGREEMENTS then local st = it:GetSubType() "
    "s = (st == DealAgreementTypes.OPEN_BORDERS and 'Open Borders') or (st == DealAgreementTypes.JOINT_WAR and 'Joint War') "
    "or (st == DealAgreementTypes.ALLIANCE and 'Alliance') or 'an agreement' if dur > 0 then s = s .. ' (' .. dur .. ' turns)' end "
    "elseif ty == DealItemTypes.FAVOR then s = amt .. ' Diplomatic Favor' "
    "elseif ty == DealItemTypes.CITIES then s = 'a city' "
    "elseif ty == DealItemTypes.GREATWORK then s = 'a Great Work' end "
    "if it:GetFromPlayerID() == me then give[#give + 1] = s else get[#get + 1] = s end end end "
    "return 'we give ' .. (#give > 0 and table.concat(give, ', ') or 'nothing') .. '; they give ' "
    ".. (#get > 0 and table.concat(get, ', ') or 'nothing') end "
)


def deal_poll_lua(target: int, mark: int) -> str:
    """Events since mark (S|from|to|action|respondingTo, E|a|b), then STATE|session|pending(me,t)|pending(t,me)."""
    return (
        DEAL_LISTENER + f"local me = Game.GetLocalPlayer() local t = {target} local d = BENCH_DEALS "
        f"for i = {mark} + 1, d.n do print('EV|' .. d[i]) end "
        "local inn = DealManager.GetWorkingDeal(DealDirection.INCOMING, me, t) "
        "print('STATE|' .. tostring((DiplomacyManager.FindOpenSessionID(me, t))) .. '|' "
        ".. tostring((DealManager.HasPendingDeal(me, t))) .. '|' .. tostring((DealManager.HasPendingDeal(t, me))) .. '|' "
        ".. tostring(inn and inn:GetItemCount() or 0)) "
        "print('---END---')"
    )


def deal_propose_lua(target: int, items_lua: str) -> str:
    """Open a deal session, build the outgoing deal and send it as PROPOSED; prints CIV|name and MARK|n."""
    return (
        DEAL_LISTENER + f"local me = Game.GetLocalPlayer() local target = {target} "
        "local pDiplo = Players[me]:GetDiplomacy() "
        "if not pDiplo:HasMet(target) then print('ERR:NOT_MET|Have not met this player') print('---END---') return end "
        "if pDiplo:IsAtWarWith(target) then print('ERR:AT_WAR|Cannot trade while at war') print('---END---') return end "
        "print('CIV|' .. Locale.Lookup(PlayerConfigurations[target]:GetCivilizationShortDescription())) "
        "DiplomacyManager.RequestSession(me, target, 'MAKE_DEAL') "
        "DealManager.ClearWorkingDeal(DealDirection.OUTGOING, me, target) "
        "local deal = DealManager.GetWorkingDeal(DealDirection.OUTGOING, me, target) "
        "if not deal then print('ERR:NO_DEAL_OBJECT|Failed to get working deal') print('---END---') return end "
        f"{items_lua} "
        "print('MARK|' .. BENCH_DEALS.n) "
        "DealManager.SendWorkingDeal(DealProposalAction.PROPOSED, me, target) "
        "print('---END---')"
    )


def deal_accept_lua(target: int, copy_incoming: bool) -> str:
    """Accept the deal in the open session: the AI's offer (copied into ours first) or our proposal it accepted.
    Prints TERMS|..., MARK|n, or NOT_EQUAL|incoming terms when the AI changed our proposal."""
    check = ("DealManager.CopyIncomingToOutgoingWorkingDeal(me, target) " if copy_incoming else
             "if not DealManager.AreWorkingDealsEqual(me, target) then "
             "print('NOT_EQUAL|' .. benchTerms(DealManager.GetWorkingDeal(DealDirection.INCOMING, me, target), me)) "
             "print('---END---') return end ")
    return (
        DEAL_LISTENER + DEAL_TERMS_FN + f"local me = Game.GetLocalPlayer() local target = {target} "
        "local sid = (DiplomacyManager.FindOpenSessionID(me, target)) "
        "if not sid or sid < 0 then print('ERR:NO_SESSION|No deal session is open with this player') print('---END---') return end "
        + check +
        "print('TERMS|' .. benchTerms(DealManager.GetWorkingDeal(DealDirection.OUTGOING, me, target), me)) "
        "print('MARK|' .. BENCH_DEALS.n) "
        "DealManager.SendWorkingDeal(DealProposalAction.ACCEPTED, me, target) "
        "print('---END---')"
    )


def deal_incoming_lua(target: int) -> str:
    """TERMS|the AI's side of the deal in the open session (its counter-offer)."""
    return (DEAL_TERMS_FN + f"local me = Game.GetLocalPlayer() "
            f"print('TERMS|' .. benchTerms(DealManager.GetWorkingDeal(DealDirection.INCOMING, me, {target}), me)) "
            "print('---END---')")


def deal_close_lua(target: int) -> str:
    """Close the player's deal session with target, as the deal view's Resume Game does (OnResumeGame)."""
    return (f"local me = Game.GetLocalPlayer() local sid = (DiplomacyManager.FindOpenSessionID(me, {target})) "
            "if sid and sid >= 0 then DiplomacyManager.CloseSession(sid) print('CLOSED|' .. sid) end "
            "print('---END---')")


def mark_test_trade(lua: str) -> str:
    """civ6-mcp's test_trade Lua, with the deal listener, a MARK before its EQUALIZE, and its closing of the session
    removed (the session is closed once the AI has answered)."""
    send = "DealManager.SendWorkingDeal(DealProposalAction.EQUALIZE, me, target)"
    close = ("pcall(function()\n    local sid = DiplomacyManager.FindOpenSessionID(me, target)\n"
             "    if sid and sid >= 0 then DiplomacyManager.CloseSession(sid) end\nend)\n")
    # The same block also closes any open session before the request; only the one after the EQUALIZE goes.
    assert lua.count(send) == 1 and lua.count(close) == 2 and lua.rindex(close) > lua.index(send), \
        "civ6-mcp's test_trade Lua changed"
    head, _, tail = lua.rpartition(close)
    lua = (head + tail).replace(send, "print('MARK|' .. BENCH_DEALS.n) " + send)
    return DEAL_LISTENER + lua


def reread_test_trade(lua: str) -> str:
    """From civ6-mcp's test_trade Lua, a call that prints the same CIV, PROPOSED_ITEMS and AI_COUNTER lines for the
    deals as they are now, without sending anything: its own read of the counter-offer comes in the same call as the
    EQUALIZE, before the AI has answered, so it shows the deal left from the last test or none."""
    send = "DealManager.SendWorkingDeal(DealProposalAction.EQUALIZE, me, target)\n"
    close = ("pcall(function()\n    local sid = DiplomacyManager.FindOpenSessionID(me, target)\n"
             "    if sid and sid >= 0 then DiplomacyManager.CloseSession(sid) end\nend)\n")
    items = 'print("PROPOSED_ITEMS")'
    assert lua.count(send) == 1 and lua.count(close) == 2 and lua.count(items) == 1, "civ6-mcp's test_trade Lua changed"
    first, last = lua.index(close), lua.rindex(close)
    return (lua[:first] + "local deal = DealManager.GetWorkingDeal(DealDirection.OUTGOING, me, target)\n"
            + lua[lua.index(items):last].replace(send, "") + lua[last + len(close):])


# When civ6-mcp closes an AI-opened diplomacy session itself (DiplomacyManager.CloseSession, as in its "goodbye
# phase" auto-close), the leader screen can stay up in its overview mode. While it is up, the AI turns never finish:
# game 1 waited 10 minutes on turn 92, reloaded the turn, and stalled again until the screen was closed by hand. A
# leader screen with no open session is closed the way it closes itself for a blocking popup (OnBlockingPopupShown in
# the base game's DiplomacyActionView.lua), as civ6-mcp does after a war declaration.
LEADER_SCREEN_LUA = (
    "local v = ContextPtr:LookUpControl('/InGame/DiplomacyActionView') "
    "if v and not v:IsHidden() then "
    "  local me = Game.GetLocalPlayer() local open = false "
    "  for _, p in ipairs(PlayerManager.GetAliveMajors()) do "
    "    local sid = p:GetID() ~= me and DiplomacyManager.FindOpenSessionID(me, p:GetID()) "
    "    if sid and sid >= 0 then open = true end "
    "  end "
    "  if open then print('LEADER_SCREEN|SESSION') else "
    "    LuaEvents.NaturalWonderPopup_Shown() LuaEvents.NaturalWonderPopup_Closed() print('LEADER_SCREEN|CLOSED') end "
    "else print('LEADER_SCREEN|HIDDEN') end "
    "print('---END---')"
)


def one_line(lua: str) -> str:
    """The prelude as one line, so line numbers in Lua errors still match civ6-mcp's own code."""
    parts = []
    for line in lua.splitlines():
        line = line.split("--", 1)[0].strip()  # the prelude has no "--" inside strings
        if line:
            parts.append(line)
    return " ".join(parts)


def load_prelude(path: str | None = None) -> str:
    with open(path or os.path.join(HERE, "base-game-compat.lua"), encoding="utf-8") as f:
        return one_line(f.read())


def base_game_rewrite(code: str, prelude: str) -> str:
    """Point expansion APIs at their CB_ stand-ins and prepend the prelude, only when something was rewritten.
    Idempotent: a chunk that already starts with the prelude comes back unchanged."""
    if code.startswith(prelude):
        return code
    new = code
    for rx, rep in RULES:
        new = rx.sub(rep, new)
    if new == code:
        return code
    return prelude + " " + new


def filter_output(text: str, rules) -> str:
    for rx, rep in rules:
        text = rx.sub(rep, text)
    return text
