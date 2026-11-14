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

def _not_available_lua(name: str, tech: bool) -> str:
    """Refuse a tech or civic the game does not offer yet (see the rule that uses it), naming the missing ones."""
    owner, can, has, table, prereqs, own, pre = (
        ("GetTechs", "CanResearch", "HasTech", "Technologies", "TechnologyPrereqs", "Technology", "PrereqTech") if tech
        else ("GetCulture", "CanProgress", "HasCivic", "Civics", "CivicPrereqs", "Civic", "PrereqCivic"))
    verb, lister = ("researched", "get_tech_civics") if tech else ("started", "get_tech_civics")
    return (
        f"do local okc, canc = pcall(function() return Players[id]:{owner}():{can}(idx) end) "
        "if okc and canc == false then local miss = {} "
        f"for p in GameInfo.{prereqs}() do if p.{own} == \"{name}\" then local r = GameInfo.{table}[p.{pre}] "
        f"if r and not Players[id]:{owner}():{has}(r.Index) then miss[#miss + 1] = Locale.Lookup(r.Name) end end end "
        f"print(\"ERR:NOT_AVAILABLE|{name} cannot be {verb} yet\" .. (#miss > 0 and (\": it needs \" .. "
        f"table.concat(miss, \", \") .. \" first\") or \"\") .. \". {lister} lists what is available now.\") "
        "print(\"---END---\") return end end\n"
    )


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
    # set_research / set_civic took a tech or civic the game does not offer yet: game 25's set_research answered
    # RESEARCHING|TECH_ECONOMICS on turn 115 without Scientific Theory, and the next turn the game asked for a tech
    # again (the agent picked Astronomy). When the game ignores a request, civ6-mcp also falls back to GameCore
    # (SetResearchingTech), which skips the prerequisites. Ask what the game's own tech and civic trees ask
    # (CanResearch, CanProgress) first, on both paths, and name what is missing.
    (re.compile(r'(print\("ERR:ALREADY_COMPLETED\|((TECH|CIVIC)_\w+) is already researched"\); '
                r'print\("---END---"\); return\s*\nend\n)'),
     lambda m: m[1] + _not_available_lua(m[2], m[3] == "TECH")),
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

# Spy travel. civ6-mcp says a spy can travel only to the player's own cities and city-states ("Allied civ cities are
# NOT valid travel targets", in spy_action's description and get_spies), and answers every refusal with "Allied civ
# cities are not valid; only own cities and city-states". In game 19 spies travelled to Greek and Spanish cities, and
# none of the three refusals was about an ally: a spy bought that turn (turn 150), a spy just back from a mission, and
# Madrid while Spain was a friend. The travel below asks the game for its reasons and says what is at the target.
SPY_TRAVEL_DOC = (re.compile(r"Travel notes:\n(?:\s*- [^\n]*\n){3}"),
                  "Travel notes:\n        - Targets: your own cities, city-states and other civs' cities. If the game "
                  "refuses, the error gives its reasons and the spy's moves left.\n"
                  "        - Travel is queued end-of-turn; spy position updates after turn ends.\n")
OUTPUT_RULES["get_spies"].append((re.compile(r" — send spy to own city or city-state"),
                                  " — send spy to a city: your own, a city-state's or another civ's"))


# The reasons the game gives for refusing a unit operation. CanStartOperation(..., true) returns them keyed by
# UnitOperationResults.FAILURE_REASONS (a hash), next to ADDITIONAL_DESCRIPTION ("Yields 125 Science" on a Spaceport),
# not under a FailureReasons field: read that way, game 19's refused pillage said "it gave no reason" where the game
# said "Not enough movement points left."
_WHY_LUA = (
    "local why = {} "
    "if ok and type(res) == 'table' then "
    "  local fr = (UnitOperationResults and res[UnitOperationResults.FAILURE_REASONS]) or res.FailureReasons "
    "  if type(fr) == 'table' then for _, r in ipairs(fr) do why[#why + 1] = (string.gsub(Locale.Lookup(tostring(r)), '%.%s*$', '')) end end "
    "end "
)


def spy_travel_lua(unit_index: int, x: int, y: int) -> str:
    """civ6-mcp's spy travel (UNITOPERATION_SPY_TRAVEL_NEW_CITY), which on a refusal reports the game's failure reasons,
    the spy's moves left and the city at the target instead of a guess."""
    return (
        f"local me = Game.GetLocalPlayer() local unit = UnitManager.GetUnit(me, {int(unit_index)}) "
        "if unit == nil then print('ERR:UNIT_NOT_FOUND') print('---END---') return end "
        "local entry = GameInfo.Units[unit:GetType()] "
        "if not entry or entry.UnitType ~= 'UNIT_SPY' then print('ERR:NOT_A_SPY') print('---END---') return end "
        f"local x, y = {int(x)}, {int(y)} "
        "local op = GameInfo.UnitOperations['UNITOPERATION_SPY_TRAVEL_NEW_CITY'] "
        "local params = {[UnitOperationTypes.PARAM_X0] = x, [UnitOperationTypes.PARAM_Y0] = y} "
        "local ok, can, res = pcall(function() return UnitManager.CanStartOperation(unit, op.Hash, nil, params, true) end) "
        "if ok and can then "
        "  UnitManager.RequestOperation(unit, op.Hash, params) "
        "  print('OK:SPY_TRAVEL|Spy en route to (' .. x .. ',' .. y .. '). Travel completes at end of turn.') "
        "  print('---END---') return "
        "end "
        + _WHY_LUA +
        "local at = 'there is no city there' "
        "local city = Cities.GetPlotPurchaseCity(x, y) "
        "if city and (city:GetX() ~= x or city:GetY() ~= y) then at = 'the tile is not a city centre (it belongs to ' "
        "  .. Locale.Lookup(city:GetName()) .. ')' city = nil end "
        "if city then "
        "  local o = city:GetOwner() local cfg = PlayerConfigurations[o] "
        "  local who = o == me and 'yours' or (Players[o]:IsMajor() and Locale.Lookup(cfg:GetCivilizationShortDescription()) "
        "    or 'a city-state') "
        "  at = 'the city there is ' .. Locale.Lookup(city:GetName()) .. ' (' .. who .. ')' "
        # the game sends no spy into an ally's cities and gives no reason (game 26: India and Greece, every city)
        "  local okA, st = pcall(function() return GameInfo.DiplomaticStates[Players[o]:GetDiplomaticAI()"
        ":GetDiplomaticStateIndex(me)].StateType end) "
        "  if o ~= me and okA and st == 'DIPLO_STATE_ALLIED' and #why == 0 then "
        "    why[1] = who .. ' is your ally, and the game sends no spies into an ally' .. string.char(39) .. 's cities "
        "while the alliance lasts' end "
        "end "
        "print('ERR:CANNOT_TRAVEL|The game will not send this spy to (' .. x .. ',' .. y .. ') now: ' "
        "  .. (#why > 0 and table.concat(why, '; ') or 'it gave no reason') .. '. The spy has ' "
        "  .. unit:GetMovesRemaining() .. ' moves left (a spy with none, for example one bought or back from a "
        "mission this turn, can travel next turn), and ' .. at .. '.') "
        "print('---END---')"
    )


# No pillage order. On turn 209 of game 19 the agent declared war on Spain to pillage its three spaceports and then
# found that civ6-mcp's unit_action had none ("the tools have no pillage action"). The game's unit panel sends
# UNITOPERATION_PILLAGE (an improvement, a district or one of its buildings) or UNITOPERATION_PILLAGE_ROUTE (a road)
# on the unit's own tile, and so does unit_action's pillage, then it reads the tile again.
PILLAGE_OPS = {"pillage": "UNITOPERATION_PILLAGE", "pillage_route": "UNITOPERATION_PILLAGE_ROUTE"}
PILLAGE_NOTE = (
    "\n\nAlso: pillage = pillage what is on the unit's own tile (an improvement, or a district or one of its "
    "buildings: a district's buildings go one per pillage, then the district) with the game's own pillage order; "
    "pillage_route = pillage the road there. Military land units, at war with the tile's owner or on a tile no civ "
    "owns. It costs 3 moves, or all of them for a unit with fewer than 3 (a Warrior or a Machine Gun must start the "
    "turn on the tile: move there this turn, pillage the next). A pillaged district produces nothing (a Spaceport "
    "builds no space projects) until its owner repairs it. "
    "The result says what the game refused, or what the tile shows afterwards."
)


def pillage_lua(unit_index: int, op_name: str) -> str:
    """Send the game's pillage order for the unit's tile, or report the game's reasons for refusing it."""
    return (
        f"local me = Game.GetLocalPlayer() local unit = UnitManager.GetUnit(me, {int(unit_index)}) "
        "if unit == nil then print('ERR:UNIT_NOT_FOUND') print('---END---') return end "
        "local x, y = unit:GetX(), unit:GetY() "
        f"local op = GameInfo.UnitOperations['{op_name}'] "
        f"if op == nil then print('ERR:NO_OP|{op_name} is not in this game') print('---END---') return end "
        "local params = {[UnitOperationTypes.PARAM_X] = x, [UnitOperationTypes.PARAM_Y] = y} "
        "local ok, can, res = pcall(function() return UnitManager.CanStartOperation(unit, op.Hash, nil, params, true) end) "
        "if ok and can then "
        "  UnitManager.RequestOperation(unit, op.Hash, params) "
        "  print('OK:PILLAGE_SENT|' .. x .. '|' .. y) print('---END---') return "
        "end "
        + _WHY_LUA +
        f"print('ERR:CANNOT_PILLAGE|The game refused {op_name} at (' .. x .. ',' .. y .. '): ' "
        "  .. (#why > 0 and table.concat(why, '; ') or 'it gave no reason') .. '. The unit has ' .. unit:GetMovesRemaining() "
        "  .. ' moves left.') "
        "print('---END---')"
    )


def pillage_tile_lua(unit_index: int) -> str:
    """What is on the unit's tile, and what of it is pillaged: TILE|x|y|moves|item=state,... (one line)."""
    return (
        f"local me = Game.GetLocalPlayer() local unit = UnitManager.GetUnit(me, {int(unit_index)}) "
        "if unit == nil then print('TILE|gone') print('---END---') return end "
        "local x, y = unit:GetX(), unit:GetY() local plot = Map.GetPlot(x, y) local t = {} "
        "local imp = plot:GetImprovementType() "
        "if imp >= 0 then t[#t + 1] = GameInfo.Improvements[imp].ImprovementType .. '=' .. "
        "  (plot:IsImprovementPillaged() and 'pillaged' or 'intact') end "
        "local o = plot:GetOwner() "
        "if o >= 0 and Players[o] then "
        "  for _, d in Players[o]:GetDistricts():Members() do "
        "    if d:GetX() == x and d:GetY() == y then "
        "      local di = GameInfo.Districts[d:GetType()] "
        "      t[#t + 1] = di.DistrictType .. '=' .. (d:IsPillaged() and 'pillaged' or 'intact') "
        "      local c = Cities.GetPlotPurchaseCity(x, y) "
        "      if c then for b in GameInfo.Buildings() do "
        "        if b.PrereqDistrict == di.DistrictType and c:GetBuildings():HasBuilding(b.Index) then "
        "          t[#t + 1] = b.BuildingType .. '=' .. (c:GetBuildings():IsPillaged(b.Index) and 'pillaged' or 'intact') "
        "        end end end "
        "    end "
        "  end "
        "end "
        "if plot:GetRouteType() >= 0 then t[#t + 1] = 'ROAD=' .. (plot:IsRoutePillaged() and 'pillaged' or 'intact') end "
        "print('TILE|' .. x .. '|' .. y .. '|' .. unit:GetMovesRemaining() .. '|' .. table.concat(t, ',')) "
        "print('---END---')"
    )

# Trade routes. civ6-mcp answers a refused route with "CanStartOperation returned false for destination (x,y)". In
# game 20 (turn 146) one Trader got that for every destination it tried, and the agent left it idle. Replayed, the game
# refused it with no reason (its own route screen makes the same CanStartOperation call), while another Trader in the
# same city could start the same routes: the refused one's last route came from Kish, which Spain took that turn, and
# it ran routes again later. The refusal now gives the game's reasons, where the Trader stands (a route starts from
# the city the Trader is in) and, when its last route's city is gone, that.
_ROUTE_REFUSED = 'print("ERR:CANNOT_START_ROUTE|CanStartOperation returned false for destination ('
_BAIL_END = 'print("---END---"); return'


def trade_route_lua(original):
    """civ6-mcp's trade route builder, whose refusal gives the game's reasons and the Trader's position."""
    def build(unit_index: int, target_x: int, target_y: int) -> str:
        lua = original(unit_index, target_x, target_y)
        i = lua.find(_ROUTE_REFUSED)
        j = lua.find(_BAIL_END, i) if i >= 0 else -1
        if i < 0 or j < 0:
            return lua  # civ6-mcp changed: its own message, unchanged
        x, y = int(target_x), int(target_y)
        why = (
            "local ok, can, res = pcall(function() return UnitManager.CanStartOperation(unit, opHash, nil, tParams, true) end) "
            + _WHY_LUA +
            "local here = CityManager.GetCityAt(unit:GetX(), unit:GetY()) "
            "local lost = '' "
            "pcall(function() local o = unit:GetTrade():GetLastOriginTradeCityComponentID() "
            "  if o and o.player == me and CityManager.GetCity(o.player, o.id) == nil then lost = ' Its last route came '"
            "    .. 'from a city you no longer hold, and the game refuses such a Trader everywhere on that turn (game 20: '"
            "    .. 'it started a route again on a later turn).' end end) "
            f"print('ERR:CANNOT_START_ROUTE|The game will not start this route to ({x},{y}): ' "
            "  .. (#why > 0 and table.concat(why, '; ') or 'it gave no reason') .. '. The Trader is at (' .. unit:GetX() "
            "  .. ',' .. unit:GetY() .. ')' .. (here and (' in ' .. Locale.Lookup(here:GetName()) .. '.') or ', not in a "
            "city: a route starts from the city the Trader is in, so move it or teleport it to one first.') .. lost) "
            "print('---END---') return"
        )
        return lua[:i] + why + lua[j + len(_BAIL_END):]
    return build



# A city's attack list named units it could not attack. get_cities lists "CAN ATTACK" targets for a city with walls:
# every unit within 3 tiles that is not the player's, at war or not, seen or not, civilians included, though a city
# strikes at range 2. In game 20 it listed a Builder (turn 77) and Brazilian units while at peace with Brazil (turn 172).
# civ6-mcp's own city attack checks the game's target list (CityManager.GetCommandTargets with RANGE_ATTACK: range,
# line of sight, and empty once the city has fired), so the list now comes from it too, keeping units of civs at war
# with the player and barbarians, and no civilians. The game's list alone is not enough: on game 20's turn-173 save it
# still held a Brazilian Machine Gun 2 tiles from Shuruppak, with Brazil at peace.
_CITY_TARGETS_START = "    local cityTargets = {}\n"
_CITY_TARGETS_END = "    local pillDistricts = {}\n"
_CITY_TARGETS_LUA = """    local cityTargets = {}
    if wallMax > 0 then
        local okT, tg = pcall(function() return CityManager.GetCommandTargets(c, CityCommandTypes.RANGE_ATTACK) end)
        if okT and type(tg) == "table" then
            local W = Map.GetGridSize()
            local dip = Players[me]:GetDiplomacy()
            local function hostile(o)
                local ok, war = pcall(function() return dip:IsAtWarWith(o) end)
                local okB, barb = pcall(function() return Players[o]:IsBarbarian() end)
                return (ok and war) or (okB and barb)
            end
            local seen = {}
            for _, tbl in pairs(tg) do if type(tbl) == "table" then for _, idx in ipairs(tbl) do
                if type(idx) == "number" and not seen[idx] then
                    seen[idx] = true
                    local tx, ty = idx % W, math.floor(idx / W)
                    local pu = Map.GetUnitsAt(tx, ty)
                    if pu then for other in pu:Units() do
                        local eInfo = GameInfo.Units[other:GetType()]
                        if other:GetOwner() ~= me and hostile(other:GetOwner())
                                and not (eInfo and eInfo.FormationClass == "FORMATION_CLASS_CIVILIAN") then
                            local eName = eInfo and eInfo.UnitType or "UNKNOWN"
                            local eHP = other:GetMaxDamage() - other:GetDamage()
                            table.insert(cityTargets, eName .. "@" .. tx .. "," .. ty .. "(" .. eHP .. "hp)")
                        end
                    end end
                end
            end end end
        end
    end
"""


def city_targets_lua(original):
    """civ6-mcp's cities query, whose CAN ATTACK list is the game's own target list for the city's ranged strike."""
    def build(*args, **kwargs) -> str:
        lua = original(*args, **kwargs)
        i = lua.find(_CITY_TARGETS_START)
        j = lua.find(_CITY_TARGETS_END, i) if i >= 0 else -1
        if i < 0 or j < 0 or lua.count(_CITY_TARGETS_START) != 1:
            return lua  # civ6-mcp changed: its own list, unchanged
        return lua[:i] + _CITY_TARGETS_LUA + lua[j:]
    return build


# Envoys: one per call, and the result did not say more were left. In game 20 the agent sent an envoy, ended the turn,
# was refused over envoys still to give, and sent a second (turns 152 and 173). civ6-mcp re-reads the count afterwards,
# but the request is asynchronous and that re-read never made it into the result. The count before the request, less
# this one, is what is left.
_ENVOY_REQUEST = "UI.RequestPlayerOperation(me, PlayerOperations.GIVE_INFLUENCE_TOKEN, params)"
_ENVOY_SENT = 'print("OK:ENVOY_SENT|" .. name)'


def send_envoy_lua(original):
    """civ6-mcp's send_envoy, whose result says how many envoys are still to give."""
    def build(city_state_player_id: int) -> str:
        lua = original(city_state_player_id)
        if lua.count(_ENVOY_REQUEST) != 1 or lua.count(_ENVOY_SENT) != 1:
            return lua  # civ6-mcp changed: its own result, unchanged
        lua = lua.replace(_ENVOY_REQUEST, "local __left = pInfluence:GetTokensToGive() - 1\n" + _ENVOY_REQUEST)
        return lua.replace(_ENVOY_SENT, (
            'print("OK:ENVOY_SENT|" .. name .. (__left > 0 and (". " .. __left .. " more envoy" .. '
            '(__left > 1 and "s" or "") .. " to give this turn: send them before end_turn") or ". No envoys left to give"))'))
    return build


# Settle sites on another civ's land. Both settle scans (get_settle_advisor around a Settler, get_global_settle_advisor
# over the map) skip water, mountains and tiles within 3 of a city, but not tiles another civ owns, where the game
# will not found a city. In game 20 the global advisor kept offering (36,36) inside Spain's borders (turn 182).
_SETTLE_TILE = "and not cPlot:IsWater() and not cPlot:IsMountain() then"


def settle_owned_lua(original):
    """A civ6-mcp settle scan that leaves out tiles another civ owns."""
    def build(*args, **kwargs) -> str:
        lua = original(*args, **kwargs)
        if lua.count(_SETTLE_TILE) != 1:
            return lua  # civ6-mcp changed: its own scan, unchanged
        return lua.replace(_SETTLE_TILE, "and not cPlot:IsWater() and not cPlot:IsMountain() "
                                         "and (cPlot:GetOwner() == -1 or cPlot:GetOwner() == me) then")
    return build

# Attacks on cities. civ6-mcp's attack looks for an enemy unit on the target tile and answers NO_ENEMY when there is
# none, so a city with no unit in it could not be attacked at all. In game 20 the agent declared war on Brazil (turn 57)
# to take Salvador da Bahia, a city with no walls and no unit, and every attack on it got "No hostile unit at (42,35)".
# It wrote "Conquest blocked by tooling", pillaged a few tiles and made peace ten turns later. The game attacks the
# tile: replayed from turn 58's save, a War-Cart's attack on Salvador took its garrison from 200 to 156. With no unit on
# the tile, the attack now takes an enemy city centre or Encampment there (a district with garrison hit points) as its
# target and goes on as civ6-mcp's attack does, with the district's hit points as the target's.
_NO_ENEMY_ANCHOR = 'if enemy == nil then\n    print("ERR:NO_ENEMY|No hostile unit at'


def _district_target_lua(x: int, y: int) -> str:
    x, y = int(x), int(y)
    return (
        "if enemy == nil then\n"
        f"    local plot = Map.GetPlot({x}, {y})\n"
        "    local owner = plot and plot:GetOwner() or -1\n"
        "    if owner >= 0 and owner ~= me and Players[owner] and plot:GetDistrictType() >= 0 then\n"
        "        local dd = nil\n"
        f"        for _, d in Players[owner]:GetDistricts():Members() do if d:GetX() == {x} and d:GetY() == {y} then dd = d end end\n"
        "        local di = dd and GameInfo.Districts[dd:GetType()]\n"
        "        local function hp(f, k) local ok, v = pcall(f, k) return (ok and v) or 0 end\n"
        "        local function total(f) return hp(f, DefenseTypes.DISTRICT_GARRISON) + hp(f, DefenseTypes.DISTRICT_OUTER) end\n"
        "        if dd and hp(function(k) return dd:GetMaxDamage(k) end, DefenseTypes.DISTRICT_GARRISON) > 0 then\n"
        "            enemy = {\n"
        "                GetOwner = function() return owner end,\n"
        "                GetMaxDamage = function() return total(function(k) return dd:GetMaxDamage(k) end) end,\n"
        "                GetDamage = function() return total(function(k) return dd:GetDamage(k) end) end,\n"
        "            }\n"
        f"            local c = Cities.GetPlotPurchaseCity({x}, {y})\n"
        "            enemyName = di.DistrictType .. (c and (' of ' .. Locale.Lookup(c:GetName())) or '')\n"
        "        elseif di then\n"
        f"            print('ERR:NO_ENEMY|No unit at ({x},{y}), and its ' .. di.DistrictType .. ' has no defences to attack '\n"
        "              .. '(only a city centre or an Encampment has). A military unit on that tile can pillage it '\n"
        "              .. '(unit_action pillage).') print('---END---') return\n"
        "        end\n"
        "    end\n"
        "end\n"
    )


def attack_lua(original):
    """civ6-mcp's attack builder, which also takes an enemy city centre or Encampment with no unit on it."""
    def build(unit_index: int, target_x: int, target_y: int) -> str:
        lua = original(unit_index, target_x, target_y)
        if lua.count(_NO_ENEMY_ANCHOR) != 1:
            return lua  # civ6-mcp changed: its own attack, unchanged
        return lua.replace(_NO_ENEMY_ANCHOR, _district_target_lua(target_x, target_y)
                           + _NO_ENEMY_ANCHOR.replace("No hostile unit at", "No hostile unit or city at"))
    return build



# Theological combat. In game 25 (Arabia, Religious goal) the agent twice sent an Apostle against another civ's
# religious unit (turns 91 and 127) and got "NO_ENEMY|No hostile unit or city at (x,y)"; it concluded the tool could not
# do theological combat and stopped trying, while India's apostles kept killing its own. civ6-mcp's attack looks for the
# target with Map.GetUnitsAt and, had it found one, would have refused a unit of a civ at peace (NOT_AT_WAR), but
# theological combat needs no war. The game's own UI (Civ6Common.lua RequestMoveOperation) starts it like a melee
# attack: MOVE_TO onto the target's tile with the ATTACK modifier. So when the attacker has religious strength, the
# attack finds a religious unit of another player on the tile by walking every player's units, checks the attack
# would not start a war (CombatManager.IsAttackChangeWarState, as the UI does), and sends that order.
_THEO_ANCHOR = "local ux, uy = unit:GetX(), unit:GetY()\n"


def _theological_lua(x: int, y: int, sentinel: str) -> str:
    x, y = int(x), int(y)

    def bail(msg_lua: str) -> str:
        return f"print({msg_lua}) print('{sentinel}') return "

    return (
        "if (unit:GetReligiousStrength() or 0) > 0 then\n"
        "    local tgt = nil\n"
        "    for pid = 0, 63 do\n"
        "        local pp = Players[pid]\n"
        "        if pid ~= me and pp and pp:GetUnits() then\n"
        "            for _, o in pp:GetUnits():Members() do\n"
        f"                if o:GetX() == {x} and o:GetY() == {y} and (o:GetReligiousStrength() or 0) > 0 then tgt = o break end\n"
        "            end\n"
        "        end\n"
        "        if tgt then break end\n"
        "    end\n"
        "    if tgt == nil then\n"
        f"        {bail(repr(f'ERR:NO_RELIGIOUS_UNIT|No religious unit of another player at ({x},{y}). Theological combat targets another religion' + chr(39) + 's Missionary, Apostle, Inquisitor or Guru on that tile; check the tile with get_map_area first.'))}\n"
        "    end\n"
        "    local ti = GameInfo.Units[tgt:GetType()]\n"
        "    local tname = ti and ti.UnitType or 'UNKNOWN'\n"
        "    local cfg = PlayerConfigurations[tgt:GetOwner()]\n"
        "    local tciv = cfg and Locale.Lookup(cfg:GetCivilizationShortDescription()) or ('player ' .. tgt:GetOwner())\n"
        "    local okr, r1 = pcall(function() return unit:GetReligionType() end)\n"
        "    local okt, r2 = pcall(function() return tgt:GetReligionType() end)\n"
        "    if okr and okt and r1 ~= nil and r1 >= 0 and r1 == r2 then\n"
        f"        {bail(chr(39) + 'ERR:SAME_RELIGION|' + chr(39) + ' .. tname .. ' + chr(39) + ' of ' + chr(39) + ' .. tciv .. ' + chr(39) + f' at ({x},{y}) spreads the same religion as your unit; theological combat is only against another religion.' + chr(39))}\n"
        "    end\n"
        "    if unit:GetMovesRemaining() <= 0 then\n"
        f"        {bail(repr('ERR:NO_MOVES|Your religious unit has no moves left this turn; attack next turn.'))}\n"
        "    end\n"
        "    local tp = {}\n"
        f"    tp[UnitOperationTypes.PARAM_X] = {x}\n"
        f"    tp[UnitOperationTypes.PARAM_Y] = {y}\n"
        "    tp[UnitOperationTypes.PARAM_MODIFIERS] = UnitOperationMoveModifiers.ATTACK\n"
        f"    local okw, war = pcall(function() return CombatManager.IsAttackChangeWarState(unit:GetComponentID(), {x}, {y}) end)\n"
        "    if okw and war ~= nil and #war > 0 then\n"
        f"        {bail(chr(39) + 'ERR:WOULD_DECLARE_WAR|The game says this attack on ' + chr(39) + ' .. tname .. ' + chr(39) + ' of ' + chr(39) + ' .. tciv .. ' + chr(39) + ' would start a war, so it was not sent. Declare war first if you mean to.' + chr(39))}\n"
        "    end\n"
        "    if not UnitManager.CanStartOperation(unit, UnitOperationTypes.MOVE_TO, nil, tp) then\n"
        f"        {bail(chr(39) + 'ERR:ATTACK_BLOCKED|The game will not let your ' + chr(39) + ' .. (GameInfo.Units[unit:GetType()].UnitType) .. ' + chr(39) + ' at (' + chr(39) + ' .. ux .. ' + chr(39) + ',' + chr(39) + ' .. uy .. ' + chr(39) + f') attack ' + chr(39) + ' .. tname .. ' + chr(39) + ' of ' + chr(39) + ' .. tciv .. ' + chr(39) + f' at ({x},{y}): it must be next to the target with moves left, and not every religious unit can start theological combat (Apostles and Inquisitors can).' + chr(39))}\n"
        "    end\n"
        "    local thp, tmax = tgt:GetMaxDamage() - tgt:GetDamage(), tgt:GetMaxDamage()\n"
        "    local mhp, mmax = unit:GetMaxDamage() - unit:GetDamage(), unit:GetMaxDamage()\n"
        "    UnitManager.RequestOperation(unit, UnitOperationTypes.MOVE_TO, tp)\n"
        f"    print('OK:THEOLOGICAL_ATTACK|target:' .. tname .. ' of ' .. tciv .. ' at ({x},{y})|pre_hp:' .. thp .. '/' .. tmax\n"
        "      .. '|your HP:' .. mhp .. '/' .. mmax .. '|ref:' .. tgt:GetOwner() .. ':' .. tgt:GetID())\n"
        f"    print('{sentinel}') return\n"
        "end\n"
    )


def theological_lua(original, sentinel: str = "---END---"):
    """civ6-mcp's attack builder, which also does theological combat when the attacking unit is a religious one."""
    def build(unit_index: int, target_x: int, target_y: int) -> str:
        lua = original(unit_index, target_x, target_y)
        if lua.count(_THEO_ANCHOR) != 1:
            return lua  # civ6-mcp changed: its own attack, unchanged
        return lua.replace(_THEO_ANCHOR, _THEO_ANCHOR + _theological_lua(target_x, target_y, sentinel))
    return build


def religious_state_lua(unit_index: int, ref: str) -> str:
    """Both sides of a theological attack after it: REL|<your HP or GONE>|<target HP or GONE> (one line)."""
    owner, uid = (int(v) for v in ref.split(":"))
    return (
        "local me = Game.GetLocalPlayer() "
        f"local u = UnitManager.GetUnit(me, {int(unit_index)}) local t = UnitManager.GetUnit({owner}, {uid}) "
        "local function hp(x) if x == nil or x:GetX() == -9999 then return 'GONE' end "
        "  return tostring(x:GetMaxDamage() - x:GetDamage()) end "
        "print('REL|' .. hp(u) .. '|' .. hp(t)) print('---END---')"
    )


_THEO_RE = re.compile(r"THEOLOGICAL_ATTACK\|target:([^|]*)\|pre_hp:(\d+)/\d+\|your HP:(\d+)/\d+\|ref:(\d+:\d+)")


def theological_ref(out: str):
    """(target, its HP before, yours before, 'owner:id') from a THEOLOGICAL_ATTACK result, or None."""
    m = _THEO_RE.search(out)
    return (m[1], int(m[2]), int(m[3]), m[4]) if m else None


def theological_report(out: str, rel_line: str, waited: float) -> str:
    """The attack's result as it played out, from the REL| line read after it."""
    ref = theological_ref(out)
    if ref is None:
        return out
    target, t0, m0, _ = ref
    p = rel_line.split("|")
    if len(p) < 3:
        return (f"THEOLOGICAL_ATTACK|target:{target}|enemy HP:{t0}|your HP:{m0}|The attack was sent, but the units "
                "could not be read back; check get_units.")
    mine = "your unit died" if p[1] == "GONE" else f"your HP:{m0} -> {p[1]}"
    theirs = "enemy HP:" + str(t0) + (" -> killed" if p[2] == "GONE" else f" -> {p[2]}")
    if p[1] != "GONE" and p[2] != "GONE" and int(p[1]) == m0 and int(p[2]) == t0:
        return (f"Error: NOT_RESOLVED|The theological attack on {target} was sent, but after {waited:.0f} seconds "
                "neither unit's HP has changed. Check get_units before you order it again.")
    note = (" Killing a religious unit adds pressure for your religion in the cities around it." if p[2] == "GONE"
            else "")
    return f"THEOLOGICAL_ATTACK|target:{target}|{theirs}|{mine}{note}"



# The culture victory count. civ6-mcp's get_victory_progress compared, civ by civ, the tourists from that civ visiting
# you with that civ's domestic tourists ("vs Egypt: 46/310 tourists (need 264 more)"). The game counts differently: its
# World Rankings screen (WorldRankings.lua GatherCultureData) takes all the tourists visiting you (GetTouristsTo) and
# needs one more than the largest domestic count of any other civ. In game 26 (France, Culture goal) the game showed
# "Your Culture Victory Imminent" on turn 220 while the tool showed every civ out of reach; the agent decided the
# tool was off but judged a culture win "unlikely given the tourist gap". The query now also prints every civ's
# visiting and domestic tourists, and the Culture section and its verdict use the game's rule.
_CULTURE_ROWS_LUA = (  # in its own function: the query already holds many locals, and Lua allows 200 per function
    "(function() local cme = Game.GetLocalPlayer() local cdip = Players[cme]:GetDiplomacy() "
    "for i = 0, 62 do local q = Players[i] if q and q:IsMajor() and q:IsAlive() then "
    "  local c = q:GetCulture() local okT, vis = pcall(function() return c:GetTouristsTo() end) "
    "  local okS, stay = pcall(function() return c:GetStaycationers() end) "
    "  local okF, from = pcall(function() return Players[cme]:GetCulture():GetTouristsFrom(i) end) "
    "  local okU, turns = pcall(function() return c:GetTurnsUntilVictory() end) "
    "  local name = 'an unmet civ' "
    "  if i == cme or cdip:HasMet(i) then name = Locale.Lookup(PlayerConfigurations[i]:GetCivilizationShortDescription()) end "
    "  print('CULTOT|' .. i .. '|' .. name .. '|' .. ((okT and vis) or -1) .. '|' .. ((okS and stay) or -1) .. '|' "
    "    .. ((okF and from) or 0) .. '|' .. ((okU and turns) or -1) .. '|' .. tostring(i == cme)) "
    "end end "
    # the score victory's turn limit: civ6-mcp writes "SCORE (highest at turn 500)" whatever the game's limit is
    "local mt = 0 pcall(function() mt = Game.GetMaxTurns() end) "
    "if (mt or 0) <= 0 then pcall(function() mt = GameConfiguration.GetMaxTurns() end) end "
    # none set (game 26 had 0): the game speed's own length, the sum of its GameSpeed_Turns rows (Online 250)
    "if (mt or 0) <= 0 then pcall(function() local sp = GameInfo.GameSpeeds[GameConfiguration.GetGameSpeedType()]"
    ".GameSpeedType mt = 0 for r in GameInfo.GameSpeed_Turns() do if r.GameSpeedType == sp then "
    "mt = mt + r.TurnsPerIncrement end end end) end "
    "print('MAXT|' .. (mt or 0)) end)() "
)


def victory_query(original):
    """civ6-mcp's victory progress query, which also prints a CULTOT row per civ for the culture count."""
    def build() -> str:
        lua = original()
        i = lua.rfind('print("---END---")')
        if i < 0:
            return lua  # civ6-mcp changed: its own query, unchanged
        return lua[:i] + _CULTURE_ROWS_LUA + "\n" + lua[i:]
    return build


def culture_rows(lines) -> list[dict]:
    """The CULTOT rows: pid, name, visiting (all tourists visiting that civ), domestic, from (visiting you from that
    civ), turns (the game's turns to a culture win, -1 when it gives none), me."""
    rows = []
    for ln in lines:
        p = ln.split("|")
        if p[0] == "CULTOT" and len(p) >= 8:
            try:
                rows.append({"pid": int(p[1]), "name": p[2], "visiting": int(float(p[3])), "domestic": int(float(p[4])),
                             "from": int(float(p[5])), "turns": int(float(p[6])), "me": p[7] == "true"})
            except ValueError:
                continue
    return rows


def max_turns(lines) -> int:
    """The game's turn limit from the MAXT row, 0 when it has none or the row is missing."""
    for ln in lines:
        if ln.startswith("MAXT|"):
            try:
                return int(float(ln.split("|")[1]))
            except ValueError:
                return 0
    return 0


def score_turn_fix(text: str, limit: int) -> str:
    """civ6-mcp's Score heading names turn 500 whatever the game's limit; name the game's own."""
    if limit <= 0:
        return text
    return text.replace("SCORE (highest at turn 500)", f"SCORE (highest at turn {limit}, this game's turn limit)", 1)


def culture_need(rows, row) -> tuple[int, str]:
    """(tourists the civ needs, the civ that sets it): one more than any other civ's domestic tourists."""
    others = [r for r in rows if r["pid"] != row["pid"]]
    if not others:
        return 1, ""
    top = max(others, key=lambda r: r["domestic"])
    return top["domestic"] + 1, top["name"]


def culture_section(rows) -> str:
    """The Culture section of get_victory_progress, by the game's rule."""
    me = next((r for r in rows if r["me"]), None)
    if me is None or me["visiting"] < 0:
        return ""
    need, by = culture_need(rows, me)
    out = ["CULTURE (the tourists visiting you from all other civs together must outnumber every other civ's domestic "
           "tourists; the game's World Rankings count)"]
    togo = need - me["visiting"]
    out.append(f"  You: {me['visiting']} visiting tourists, need {need} (one more than {by}'s {need - 1} domestic): "
               + ("you meet it" if togo <= 0 else f"{togo} to go")
               + (f", the game says {me['turns']} turns to a culture win" if me["turns"] > 0 else "") + ".")
    out.append(f"  Your domestic tourists: {me['domestic']}. A rival needs more visiting tourists than this, and than "
               "every other civ's domestic count, to win on culture.")
    rivals = []
    for r in sorted((r for r in rows if not r["me"]), key=lambda r: r["visiting"], reverse=True):
        n, _ = culture_need(rows, r)
        rivals.append(f"{r['name']} {r['visiting']}/{n}")
    out.append("  Rivals, visiting tourists / needed: " + ", ".join(rivals) + ".")
    frm = [f"{r['name']} {r['from']}" for r in sorted(rows, key=lambda r: r["from"], reverse=True) if not r["me"]]
    out.append("  Tourists visiting you, by home civ: " + ", ".join(frm) + ".")
    return "\n".join(out)


def culture_reason(rows):
    """The Culture verdict's reason, by the game's rule, or None."""
    me = next((r for r in rows if r["me"]), None)
    if me is None or me["visiting"] < 0:
        return None
    need, by = culture_need(rows, me)
    togo = need - me["visiting"]
    if togo <= 0:
        return f"{me['visiting']}/{need} visiting tourists: you meet the culture condition"
    return f"{me['visiting']}/{need} visiting tourists, {togo} to go ({by} has the most domestic tourists)"


def culture_scoring(rows, their_staycationers: dict) -> dict | None:
    """What civ6-mcp's verdict should compare: {civ: your visiting tourists - 1} against each civ's domestic count, so
    its gap (domestic - this) is at most 0 exactly when you have one more than every civ's domestic tourists."""
    me = next((r for r in rows if r["me"]), None)
    if me is None or me["visiting"] < 0:
        return None
    return {name: me["visiting"] - 1 for name in their_staycationers}


_VENDOR_CULTURE_RE = re.compile(r"CULTURE \(your tourists > every civ's domestic tourists\)\n(?:  [^\n]*(?:\n|$))*")
_VENDOR_VERDICT_RE = re.compile(r"^(  Culture +\[[#-]{10}\] \d+% — )([^\n]*?)((?: \*\* RECOMMENDED \*\*)?)$", re.M)


def culture_fix(text: str, rows) -> str:
    """Replace civ6-mcp's Culture section and its verdict's reason with the game's count; unchanged without rows."""
    section = culture_section(rows)
    if not section:
        return text
    text, n = _VENDOR_CULTURE_RE.subn(lambda m: section + "\n", text, count=1)
    if n == 0:
        return text
    reason = culture_reason(rows)
    if reason:
        text = _VENDOR_VERDICT_RE.sub(lambda m: m[1] + reason + m[3], text, count=1)
    return text

def district_state_lua(x: int, y: int) -> str:
    """The district at (x, y) after an attack: DEF|owner|is it the player's|garrison hp/max|walls hp/max (one line)."""
    x, y = int(x), int(y)
    return (
        f"local me = Game.GetLocalPlayer() local o = Map.GetPlot({x}, {y}):GetOwner() local out = 'DEF|' .. o .. '|' .. "
        "tostring(o == me) "
        "if o >= 0 and Players[o] then for _, d in Players[o]:GetDistricts():Members() do "
        f"  if d:GetX() == {x} and d:GetY() == {y} then "
        "    local function hp(k) local ok1, m = pcall(function() return d:GetMaxDamage(k) end) "
        "      local ok2, g = pcall(function() return d:GetDamage(k) end) m = (ok1 and m) or 0 "
        "      return (m - ((ok2 and g) or 0)) .. '/' .. m end "
        "    out = out .. '|' .. hp(DefenseTypes.DISTRICT_GARRISON) .. '|' .. hp(DefenseTypes.DISTRICT_OUTER) "
        "  end end end "
        "print(out) print('---END---')"
    )


CITY_ATTACK_NOTE = (
    "\n\nAlso: attack takes an enemy city centre or Encampment with no unit in it as its target too (melee or "
    "ranged, at war with its owner). A city falls to a melee unit's attack once its garrison is at 0 (walls take the "
    "damage first); ranged units cannot take it."
)


# civ6-mcp's report after an attack counts the units left on the target tile, and with none it says the target was
# killed: a city with no unit read "damage dealt:200 (killed) ... Target eliminated" after one hit.
_KILLED_RE = re.compile(r"\|damage dealt:\d+ \(killed\)")


def city_attack_report(out: str, def_line: str) -> str:
    """Replace civ6-mcp's "killed" for a district target with what the district shows after the attack."""
    out = _KILLED_RE.sub("", out)
    p = def_line.split("|")
    if len(p) >= 3 and p[2] == "true":
        now = "you hold the tile now: the city is yours (answer the keep or raze choice with city_action if asked)."
    elif len(p) >= 5:
        now = (f"garrison {p[3]}, walls {p[4]}. A city falls to a melee unit's attack once its garrison is at 0 "
               f"(walls take the damage first); ranged units cannot take it.")
    else:
        now = "the district could not be read back."
    if len(p) >= 3 and p[2] == "true":  # a taken city's hit points start again for its new owner
        out = re.sub(r"enemy HP:(\d+) -> \d+/\d+", lambda m: f"enemy HP:{m[1]} -> taken", out)
    elif len(p) >= 5:  # civ6-mcp read the hit points in the frame of the attack, before it played out
        try:
            (gh, gm), (wh, wm) = (map(int, p[3].split("/")), map(int, p[4].split("/")))
            out = re.sub(r"enemy HP:(\d+) -> \d+/\d+", lambda m: f"enemy HP:{m[1]} -> {gh + wh}/{gm + wm}", out)
        except ValueError:
            pass
    return re.sub(r"\n  Post-combat: [^\n]*", "", out) + "\n  Post-combat: " + now


# A melee attack the game did not carry out. In game 21 the agent noted six times that melee attacks into hills,
# forest or across a river "fail silently" (turns 40, 41, 62, 66, 80, 95). Moved next to the target with moves left,
# the result said "It can attack again this turn", and the attack from there came back as MELEE_ATTACK with civ6-mcp's
# estimate ("est damage dealt:~100 ... Post-combat: ~0/100 (estimate)") while the target's HP had not changed: the
# game had refused it. civ6-mcp falls back to its estimate whenever its read 0.5 s after the attack shows no change.
SHORT_OF_MOVES = ("most likely too few for the target's tile (hills, forest, marsh or a river crossing cost more), "
                  "so another attack this turn will probably fail too. Attack next turn, when the unit has all its "
                  "moves, or with another unit.")
_EST_MELEE_RE = re.compile(r"^MELEE_ATTACK\|[^\n]*\|est damage dealt:~\d+", re.M)


def melee_estimated(out: str) -> bool:
    """True when civ6-mcp's melee result is its estimate: its own read showed no change to the target."""
    return bool(_EST_MELEE_RE.search(out))


# A spy's discovered mission. The game asks its owner to pick an escape route, and civ6-mcp picks one by itself
# while it ends the turn (end_turn.py: the fastest district the city has), but only logs it ("Auto-resolved spy
# escape: OK:ESCAPE_ROUTE|Sherzi escaping via DISTRICT_CITY_CENTER"). In game 21 the agent saw the prompt it could
# not answer ("The Choose Escape Route notification can't be handled via the tools"), then no spy, twice.
def escape_note(lines: list[str]) -> str:
    """The end_turn note for the escape routes civ6-mcp picked during the turn end."""
    notes = []
    for ln in lines:
        m = re.search(r"OK:ESCAPE_ROUTE\|(.+?) escaping via (DISTRICT_\w+)", ln)
        if m:
            where = m[2].removeprefix("DISTRICT_").replace("_", " ").title()
            notes.append(f"Your spy {m[1]} was discovered on its mission, and the game asked for an escape route: "
                         f"the harness chose the {where}, the fastest the city offers.")
    if not notes:
        return ""
    return ("Spy escape: " + " ".join(notes) + " Whether the spy gets away is the game's roll: a spy that escapes "
            "comes back to you, and a caught one is gone. It may not show in get_spies while it travels.")


# No going back (civ_mcp_http._no_going_back has why): saves are named for their turn (0_MCP_0200, AutoSave_0200).
NO_GOING_BACK_NOTE = (
    "\n\nIn this benchmark a game does not go back: a save from a turn earlier than the highest turn the game has "
    "reached is refused. Reload only to recover a game that hung or crashed, from a save of the current turn."
)
_SAVE_TURN_RE = re.compile(r"_(\d{3,4})$")
_LISTED_SAVE_RE = re.compile(r"^\s*(\d+)\.\s+(\S+)", re.M)


def save_turn(name: str | None) -> int | None:
    m = _SAVE_TURN_RE.search(name or "")
    return int(m[1]) if m else None


def save_at_index(listing: str, index: int) -> str | None:
    """The save name at a 1-based index of civ6-mcp's list_saves text ("  9. 0_MCP_0200")."""
    return next((n for i, n in _LISTED_SAVE_RE.findall(listing or "") if int(i) == index), None)


def turn_in_result(out: str) -> int | None:
    """The game turn a result shows: end_turn's "Turn 222 -> 223", or an overview's leading "Turn 204 |"."""
    moves = [int(b) for _, b in re.findall(r"Turn (\d+) -> (\d+)", out[:2000])]
    if moves:
        return max(moves)
    m = re.match(r"\s*Turn (\d+) \|", out)
    return int(m[1]) if m else None


def earlier_turn_refusal(name: str | None, top: int) -> str:
    """The refusal for loading a save older than the highest turn reached, or "" when the load may go ahead."""
    if top <= 1 or name is None:  # no turn played yet, or the most recent autosave (no name given)
        return ""
    turn = save_turn(name)
    if turn is not None and turn >= top:
        return ""
    what = f"is from turn {turn}" if turn is not None else "is not a save of a turn of this game"
    return (f"Error: EARLIER_TURN|{name} {what}, and this game has reached turn {top}. In this benchmark a game does "
            f"not go back: play on from turn {top}. Reload only a game that hung or crashed, from a save of turn "
            f"{top} (AutoSave_{top:04d}, or 0_MCP_{top:04d} once that turn has ended).")


# Government changes. civ6-mcp's change_government called the game's RequestChangeGovernment with none of the checks
# of the game's Government screen (GovernmentScreen.lua, IsAbleToChangeGovernment and OnGovernmentSelected): a change
# only on a turn a civic was completed, once that turn, none during Anarchy, and a confirmation when the change brings
# Anarchy. Going back to a government the player has had before does: "Having tried X before, the people are wary of a
# return to this government", at least 3 turns with no gold, science, culture or faith (Civilopedia, Anarchy). Its
# description even said a switch after unlocking a new tier is free. In game 22 Sonnet switched to Communism (turn 201),
# back to Classical Republic (turn 203), read GOVERNMENT_CHANGED, found its yields at 0, took that for a bug and loaded
# its turn-200 save. GetAnarchyTurns(government) is read only outside Anarchy: called during Anarchy it closed the game.
_GOV_NAME_RE = re.compile(r"^[A-Z0-9_]+$")

NO_FREE_SWITCH_NOTE = (
    "\n\nThe game allows a government change only on a turn you complete a civic, once that turn, and none during "
    "Anarchy. Going back to a government you have had before brings at least 3 turns of Anarchy: no government, no "
    "gold, science, culture or faith, and policies with no effect. This tool warns before such a switch; calling it "
    "again with the same government on the same turn confirms it. A government you have never had brings none.")


def gov_state_lua(gov_type: str) -> str:
    """One GOVSTATE| line: turn|current|anarchy|anarchyEnd|civicDone|changeMade|canAtAll|anarchyTurns|usable|name|civic."""
    gov = gov_type if _GOV_NAME_RE.match(gov_type or "") else ""
    return (
        "local me = Game.GetLocalPlayer() local c = Players[me]:GetCulture() "
        f"local row = GameInfo.Governments['{gov}'] "
        "local an = c:IsInAnarchy() local turns = -1 "
        "local usable = row ~= nil and c:IsGovernmentUnlocked(row.Index) and row.Index ~= c:GetCurrentGovernment() "
        "if usable and not an then turns = c:GetAnarchyTurns(row.Index) end "
        "local civ = c:GetProgressingCivic() local civName = '' "
        "if civ and civ >= 0 and GameInfo.Civics[civ] then civName = Locale.Lookup(GameInfo.Civics[civ].Name) end "
        "print('GOVSTATE|' .. Game.GetCurrentGameTurn() .. '|' .. c:GetCurrentGovernment() .. '|' .. tostring(an) "
        "  .. '|' .. c:GetAnarchyEndTurn() .. '|' .. tostring(c:CivicCompletedThisTurn()) .. '|' "
        "  .. tostring(c:GovernmentChangeMade()) .. '|' .. tostring(c:CanChangeGovernmentAtAll()) .. '|' .. turns "
        "  .. '|' .. tostring(usable) .. '|' .. (row and Locale.Lookup(row.Name) or '') .. '|' .. civName) "
        "print('---END---')"
    )


def parse_gov_state(lines) -> dict | None:
    for ln in lines or []:
        if ln.startswith("GOVSTATE|"):
            p = ln.split("|", 11)
            if len(p) < 12:
                return None
            try:
                return {"turn": int(p[1]), "current": int(p[2]), "anarchy": p[3] == "true", "anarchy_end": int(p[4]),
                        "civic_done": p[5] == "true", "change_made": p[6] == "true", "can_at_all": p[7] == "true",
                        "anarchy_turns": int(p[8]), "usable": p[9] == "true", "name": p[10], "civic": p[11]}
            except ValueError:
                return None
    return None


def gov_change_refusal(st: dict | None, gov: str, confirmed: bool) -> str:
    """Why the game's Government screen would not make this change now, or "" when it would (or the state is unknown)."""
    if not st:
        return ""
    if st["anarchy"]:
        return (f"Error: IN_ANARCHY|Your civilization is in Anarchy until turn {st['anarchy_end']}: no government, and "
                "no gold, science, culture or faith. The game allows no government change until it ends.")
    if not st["usable"]:
        return ""  # not unlocked, already current or unknown: civ6-mcp says which
    if not st["can_at_all"] or st["change_made"] or not st["civic_done"]:
        why = ("You already changed government this turn. " if st["change_made"] else
               "No civic was completed this turn. " if st["can_at_all"] else "")
        nxt = (f" The next chance is the turn your current civic, {st['civic']}, completes." if st["civic"] else
               " No civic is in progress: choose one with set_research (category civic).")
        return (f"Error: GOV_CHANGE_NOT_NOW|{why}The game allows a government change only on a turn you complete a "
                f"civic, once that turn (its Government screen offers none otherwise).{nxt if not st['change_made'] else ''}")
    if st["anarchy_turns"] > 0 and not confirmed:
        name = st["name"] or gov
        return (f"Error: ANARCHY_WARNING|You have had {name} before, and going back to it brings {st['anarchy_turns']} "
                f"turns of Anarchy: no government, no gold, science, culture or faith, policies with no effect, and no "
                f"government change until it ends. A government you have never had brings none. To switch anyway, "
                f"call change_government with {gov} again this turn.")
    return ""


def gov_after_note(st: dict | None) -> str:
    if st and st["anarchy"]:
        return (f". ANARCHY until turn {st['anarchy_end']}: no government, and no gold, science, culture or faith "
                "until then.")
    return ""


# War declarations. civ6-mcp reads the war state in the same Lua call that sends the declaration, before the game has
# committed it, so every declaration in game 24 came back WARN:WAR_UNCERTAIN ("not yet confirmed ... Check next
# turn"). Eight of its nine took effect; the one on America on turn 115 did not, and the agent learned it only from a
# refused attack the next turn. The state read again in a call of its own, a moment later, says which it was.
def war_state_lua(other_player_id: int) -> str:
    """One WARSTATE|atWar|name line for the local player and that player."""
    t = int(other_player_id)
    return (
        f"local me = Game.GetLocalPlayer() local t = {t} local d = Players[me]:GetDiplomacy() "
        "local cfg = PlayerConfigurations[t] "
        "local name = cfg and Locale.Lookup(cfg:GetCivilizationShortDescription()) or ('player ' .. t) "
        "local st = '' pcall(function() st = GameInfo.DiplomaticStates[Players[t]:GetDiplomaticAI()"
        ":GetDiplomaticStateIndex(me)].StateType end) "
        "print('WARSTATE|' .. tostring(d:IsAtWarWith(t)) .. '|' .. name .. '|' .. st) print('---END---')"
    )


def parse_war_state(lines) -> dict | None:
    for ln in lines or []:
        if ln.startswith("WARSTATE|"):
            p = ln.split("|")
            if len(p) >= 3 and p[1] in ("true", "false"):
                return {"at_war": p[1] == "true", "name": p[2], "state": p[3] if len(p) > 3 else ""}
    return None


def war_result(out: str, st: dict | None) -> str:
    """civ6-mcp's answer to a war declaration, settled by the state read after it ("" when it needs another look)."""
    if not out.startswith("WARN:WAR_UNCERTAIN") or st is None:
        return out
    if st["at_war"]:
        return f"OK:WAR_DECLARED|At war with {st['name']} (the game's war state, read after the declaration)."
    return ""


# A refused declaration. civ6-mcp answered every refusal with "Possible reasons: friendship/alliance active, 10-turn
# peace cooldown, or target is invalid." In game 26 the agent sent war on Greece, its ally since turn 226, on turns
# 240, 241 and 242 while Greece finished the space race, each time with that answer. Replayed from turn 240's save,
# the game's CanDeclareWarOn was false for each civ France was allied with or had declared friendship with, and true
# for the others: the refusal now names the state with that civ.
def war_refused(out: str, st: dict | None) -> str:
    if st is None:
        return out
    name, state = st["name"], st.get("state", "")
    if state == "DIPLO_STATE_ALLIED":
        why = (f"you are allied with {name}, and the game allows no war on an ally while the alliance lasts "
               "(get_diplomacy shows the state with each civ).")
    elif state == "DIPLO_STATE_DECLARED_FRIEND":
        why = (f"you have a declared friendship with {name}, and the game allows no war on a declared friend while "
               "it lasts (get_diplomacy shows the state with each civ).")
    else:
        why = (f"the game gives no reason, and your relation with {name} is "
               f"{state.replace('DIPLO_STATE_', '').replace('_', ' ').lower() or 'unknown'}. A peace deal blocks war "
               "for 10 turns after it is signed.")
    return f"Error: CANNOT_DECLARE_WAR|The game will not let you declare war on {name} now: {why}"


def war_not_declared(action: str, st: dict) -> str:
    return (f"Error: WAR_NOT_DECLARED|The game still shows peace with {st['name']} a few seconds after the declaration: "
            f"{action} did not take effect. Send it again; units cannot attack {st['name']} until the war is on.")


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
    """Open a deal session, build the outgoing deal and send it as PROPOSED; prints CIV|name, TERMS|the deal as sent
    and MARK|n. An AI that accepts it answers ACCEPTED and the game enacts the deal then, with no ACCEPTED from the
    player (live, game 12 turn 96: the statement and DiplomacyDealEnacted came together; civ6-mcp's extra ACCEPTED
    enacted the same deal a second time)."""
    return (
        DEAL_LISTENER + DEAL_TERMS_FN + f"local me = Game.GetLocalPlayer() local target = {target} "
        "local pDiplo = Players[me]:GetDiplomacy() "
        "if not pDiplo:HasMet(target) then print('ERR:NOT_MET|Have not met this player') print('---END---') return end "
        "if pDiplo:IsAtWarWith(target) then print('ERR:AT_WAR|Cannot trade while at war') print('---END---') return end "
        "print('CIV|' .. Locale.Lookup(PlayerConfigurations[target]:GetCivilizationShortDescription())) "
        "DiplomacyManager.RequestSession(me, target, 'MAKE_DEAL') "
        "DealManager.ClearWorkingDeal(DealDirection.OUTGOING, me, target) "
        "local deal = DealManager.GetWorkingDeal(DealDirection.OUTGOING, me, target) "
        "if not deal then print('ERR:NO_DEAL_OBJECT|Failed to get working deal') print('---END---') return end "
        f"{items_lua} "
        "print('TERMS|' .. benchTerms(deal, me)) "
        "print('MARK|' .. BENCH_DEALS.n) "
        "DealManager.SendWorkingDeal(DealProposalAction.PROPOSED, me, target) "
        "print('---END---')"
    )


def deal_accept_lua(target: int, only_if_equal: bool = False) -> str:
    """Accept the AI's deal in the open session the way the deal view does: copy it into the player's working deal,
    then send ACCEPTED. Prints TERMS|... and MARK|n. With only_if_equal (the AI answered our proposal with ADJUSTED),
    only when its version is the one we proposed; otherwise prints NOT_EQUAL|its terms and sends nothing. Live, game
    12 turn 98: Greece answered ADJUSTED with the same items, and this accepted it (enacted once)."""
    check = ("if not DealManager.AreWorkingDealsEqual(me, target) then "
             "print('NOT_EQUAL|' .. benchTerms(DealManager.GetWorkingDeal(DealDirection.INCOMING, me, target), me)) "
             "print('---END---') return end ") if only_if_equal else ""
    return (
        DEAL_LISTENER + DEAL_TERMS_FN + f"local me = Game.GetLocalPlayer() local target = {target} "
        "local sid = (DiplomacyManager.FindOpenSessionID(me, target)) "
        "if not sid or sid < 0 then print('ERR:NO_SESSION|No deal session is open with this player') print('---END---') return end "
        + check + "DealManager.CopyIncomingToOutgoingWorkingDeal(me, target) "
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


def deal_clear_lua(target: int) -> str:
    """Empty the player's two working deals with target once a trade call is over (CLEARED), unless a session is open
    or the civ holds a deal toward the player (KEPT). civ6-mcp lists the incoming working deal with every session a
    civ opens, statements too, and a closed session leaves it filled: in game 15 the Coffee-for-100-gold test Egypt
    refused on turn 95 came back as 'Deal from Egypt' with its agenda complaint on turn 100, 'you settle too close'
    on turn 106 and a denouncement on turn 114. The agent accepted it all three times, and no gold came."""
    return (f"local me = Game.GetLocalPlayer() local t = {target} local sid = (DiplomacyManager.FindOpenSessionID(me, t)) "
            "if (sid and sid >= 0) or DealManager.HasPendingDeal(t, me) then print('KEPT') else "
            "DealManager.ClearWorkingDeal(DealDirection.INCOMING, me, t) "
            "DealManager.ClearWorkingDeal(DealDirection.OUTGOING, me, t) print('CLEARED') end "
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


def inspect_test_trade(lua: str) -> str:
    """mark_test_trade's Lua with INSPECT in place of EQUALIZE: the check the deal view sends as the player changes a
    deal (its auto-propose), whose answer, ACCEPTED or REJECTED, decides whether it offers Accept. It enacts nothing.
    An EQUALIZE answer that gives our terms back unchanged says nothing: on game 14's turn 107 Rome gave back Coffee
    for 4 and for 30 gold per turn, and for 60 gold, unchanged, then refused each as a proposal. INSPECT's yes held
    when proposed (America's Coffee at 4 gold per turn, Rome's Citrus at 3). Its no is strict: some of those proposals
    still went through as an ADJUSTED answer with our terms (Rome's Tea at 6, one above its INSPECT limit, and
    Spain's Truffles at 1), others were refused (Rome's Coffee at 4)."""
    return mark_test_trade(lua).replace("DealProposalAction.EQUALIZE", "DealProposalAction.INSPECT")


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
