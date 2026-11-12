# Game 19: Opus 5.5 on King, goal: Science victory, Online speed

**Result: Science victory on turn 218, 5th of 8 in score.** Game 19 puts Opus 5.5 (high effort) on King, the level where Fable 5.2 won game 17 (turn 170), one above Prince, where Opus won games 3, 7, 8 and 10 (turns 212, 206, 224 and 200). Everything else is the same: Sumeria (Gilgamesh) against the same 7 built-in AI civs on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. The start is game 17's. The fifth space project finished as turn 218 ended. The agent counts that as turn 219; the other games count the last turn played, as here. It was close: Greece and America had 4 of the 5 projects each, and Germany and Spain 3. The harness is game 18's, with the screenshot fix (only the requested game's turns are saved).

| | |
|---|---|
| Played | 2026-11-12 10:08 to 16:33 CET, 6.4 hours wall clock, about 1 hour 10 minutes of it in 5 stalled end turns (turn 41 once, turn 86 four times, below) |
| Turns | 218 (median 68 s per turn) |
| API-equivalent cost | **$64.28** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 382K output, 220M cache read, 1.57M cache write, 2.4K uncached input |
| API requests | 1,181 (about 5.4 per turn) |
| Tool calls | 1,650, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 4 times |

Cache reads are 69% of the bill ($44.08), cache writes 20% ($12.55) and output 12% ($7.64). By 50-turn range the game cost $7.88, $17.31, $16.21, $15.47 and $7.40 (turns 201 to 218, plus the closing summary).

## Final standings (turn 218)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Germany | **607** | **16** | **320** | 61 | **51** | **1,587** | 3 |
| Egypt | 550 | 11 | 145 | 53 | **51** | 571 | 0 |
| Brazil | 497 | 9 | 131 | 52 | **51** | 364 | 0 |
| America | 474 | 9 | 212 | 66 | 38 | 954 | 4 |
| **Sumeria (Opus 5.5, winner)** | **470** | **9** | **294** | **68** | **40** | **479** | **4, then 5** |
| Rome | 465 | 12 | 108 | 47 | **51** | 898 | 0 |
| Spain | 458 | 7 | 234 | 63 | **51** | 127 | 3 |
| Greece | 451 | 10 | 259 | **68** | 37 | 2 | 4 |

## How it went

The start was slow: 2 cities at turn 25 and 3 at turn 50, when Opus was last in score (64) with 12 techs to Greece's 15. Barbarians pillaged Uruk's Campus and farms around turn 55. It then settled fast, with 9 cities by turn 94, and kept all 9 to the end. No civ declared war on it. It made friends and then allies of its neighbors: Germany and Spain on turn 80 (Germany's alliance came with Horses, Mercury and gold), later Brazil and Rome. Egypt denounced it twice (turn 25, for its weak military, and turn 66, as a friend of Egypt's enemy Spain). From turn 82 its science per turn was the highest of any civ most turns up to turn 188, and again from 199 to 215 (82 at turn 100, 264 at turn 150), but it never got clear in techs: 8 behind Greece at turn 100 (27 to 35), level at turn 150 (45 each), and within 3 of the leader from turn 140 to the end, never more than 1 ahead. In score it was 7th at turn 100, 6th at turn 150, 4th at turns 175 and 200 and 5th at the end.

Greece finished the first space project on turn 153. Opus's came on turn 165, its second on turn 188, the third on turn 211 and the fourth on turn 214; by then four AI civs had started the race (Greece, Spain, America and Germany each had 3 or 4 by the end). From turn 150 it sent spies to set back the Greek and then the Spanish spaceports: one Disrupt Rocketry mission succeeded (Argos, turn 175), and four spies were killed (at Sparta on turns 158 and 169, near Madrid on turn 205 and at Valladolid on turn 208). On turn 209 it declared war on Spain, which had 3 projects, to pillage its three spaceports, and then found it had no pillage order (below). Its Machine Guns took Madrid's walls from 400 to 388, it lost two of them and its War-Cart, and Spanish units pillaged Sippar's University and Research Lab and Lagash's Workshop. Spain offered peace with Iron and 5 gold per turn on turn 217, and Opus accepted. What decided the race was the last project in Nippur, the slowest of its three spaceport cities: new mines and lumber mills, domestic trade routes into Nippur, a Factory in Eridu, a Power Plant bought for 1,040 gold and three envoys to Brussels cut Mars Hydroponics from 22 turns to about 9. It finished as turn 218 ended. America reached its fourth project the same turn, and Greece had had 4 since turn 215.

## Opus 5.5 on Prince and King, and Fable 5.2 on King

| | Game 10 (Opus 5.5, Prince) | **Game 19 (Opus 5.5, King)** | Game 17 (Fable 5.2, King) |
|---|---|---|---|
| Result | Science victory, turn 200 | **Science victory, turn 218** | Science victory, turn 170 |
| Turn 50: score / cities / techs (best AI) | 77 / 4 / 14 (15) | **64 / 3 / 12 (15)** | 74 / 4 / 13 (15) |
| Turn 100: score / cities / science / techs (best AI) | 233 / 8 / 137 / 31 (30) | **206 / 9 / 82 / 27 (35)** | 238 / 8 / 101 / 31 (35) |
| Turn 150: score / cities / science / techs (best AI) | 346 / 8 / 226 / 48 (41) | **325 / 9 / 264 / 45 (45)** | 396 / 8 / 317 / 57 (48) |
| Turn 200: score / science / techs (best AI) | 446 / 331 / 67 (61) | **443 / 235 / 67 (68)** | (game over) |
| Tech lead over the best AI at the end | +6 | **0** | +14 |
| Its space projects (turn reached) | 1 (161), 2 (179), 3 (184), 4 and 5 (200) | **1 (165), 2 (188), 3 (211), 4 (214), 5 (218)** | 1 (145), 2 (157), 3 (160), 4 (168), 5 (169) |
| Best AI's space projects at the end | 2 (Greece) | **4 (Greece, America)** | 2 (Spain) |
| Cities lost | none | **none** | none |
| Final score and rank | 446, 2nd of 8 | **470, 5th of 8** | 442, 1st of 8 |
| Cost (per turn) | $58.24 ($0.291) | **$64.28 ($0.295)** | $71.03 ($0.418) |
| Wall clock (median per turn) | 5.5 h (62 s) | **6.4 h, about 5.2 h without the stalls (68 s)** | 5.3 h (88 s) |

Opus won on King, but only just, and 18 turns later than its best Prince game. Its first 50 turns were the slowest of the three games here (3 cities and 12 techs), and the King AI civs were 8 techs ahead by turn 100, where on Prince Opus led by 1. It made up the gap in science per turn by turn 150 but never pulled ahead in techs, so the space race was a race to the end: on Prince the best AI civ had 2 projects when Opus won, here two had 4. Fable 5.2 on the same King start had 31 techs at turn 100 to Opus's 27 and won 48 turns sooner, for about $7 more. With game 17, both models have now won on King; Fable 5.2 lost on Emperor (games 16 and 18) and Opus on Deity (game 5).

## The harness in this game

From the server log and the agent's tool results:

- **5 stalled end turns, about 1 hour 10 minutes in all.** When the turn does not change, civ6-mcp waits 10 minutes, calls the AI turn stuck, reloads the turn's own save and ends the turn again. Turn 41 stalled once; the agent replayed it and the turn ended (14 minutes). Turn 86 stalled four times: three times after the automatic reload, and once more after the agent restarted the game and loaded the turn-86 save itself, though it changed its turn-86 orders each time (other research, another build). It then loaded the turn-85 save, played turn 85 with a few other orders (an Archer upgrade, a farm), and turn 86 ended normally (turns 85 and 86 took 58 minutes). Replayed afterwards from turn 85's save with the agent's first orders, turn 86 stuck the same way, and no AI turn had hung: the game had dropped the end-turn request. 90 s after it the player's turn was still open, nothing blocked it and no AI civ was moving, and a second request ended the turn at once. Turn 41 was not replayed. These are the first such stalls since game 13 (games 12 and 13 had three and two). From game 20 a dropped request is sent again after 8 s, and the second stall of a turn tells the agent to replay the turn before. Replayed with that change, the request was dropped again, sent again 11 s later, and turn 86 ended in 77 s instead of 593.
- **No pillage order.** civ6-mcp's unit actions had no pillage, so the agent's war on Spain (turn 209) to pillage its spaceports could not do what it was declared for. From game 20, `unit_action` has `pillage` and `pillage_route`. Tested on this game's turn-210 save, a Warrior pillaged Cádiz's Spaceport on the turn after it moved onto it: pillage costs 3 moves, or all of a 2-move unit's moves.
- **Misleading spy messages.** Three times a spy's travel was refused with "Allied civ cities are not valid; only own cities and city-states", though none of the three targets was an ally: a spy bought that turn (turn 150), a spy just back from a mission, and Madrid while Spain was a friend. The first time, the agent guessed the real cause (a spy with no moves left) and tried again the next turn. And the turn report said a spy "was killed" at Isin, the agent's own city, on turns 197 and 203: a spy gets a new unit ID when it travels, and the old ID's disappearance read as a death. The agent recorded one of them as a spy lost at Madrid. Both are fixed from game 20.
- **One end turn refused over a unit, reported in 70 s** (turn 138).
- **Trades**: the agent tested 9 trades (5 for resources, all refused, and 4 joint wars on Greece with Germany and Brazil, all with no answer) and proposed none. It answered 17 AI offers: 15 accepted, among them alliances with Germany, Spain, Brazil and Rome and the peace with Spain, and 2 refused.
- **Leader screens**: the harness closed a leader screen left open after a diplomacy answer 35 times, and left one alone 60 times because a diplomacy session was still open.
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 67 pauses; 19 times the game had already moved to the next turn, and none of those turns ended with no unit order.
- **Moves** said "arrived with no moves left" 85 times. **Move-and-attack** left 3 `STOPPED_SHORT`. **Auto-explore** was sent again 42 times, and `skip_remaining_units` left units with orders of their own alone in all 158 of its calls.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 219 is the agent's closing summary after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150, 200 and 218 (game window on top, war room below).
