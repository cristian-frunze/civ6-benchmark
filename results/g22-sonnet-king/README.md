# Game 22: Sonnet 5.5 on King, goal: Science victory, Online speed

**Result: Science victory on turn 223, 5th of 8 in score.** Game 22 puts Sonnet 5.5 (high effort) on King, the level Fable 5.2 (game 17, turn 170) and Opus 5.5 (game 19, turn 218) both won, one above Prince, where Sonnet won games 6 and 13 (turns 223 and 219). Everything else is the same: Sumeria (Gilgamesh) against the same 7 built-in AI civs on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. The harness is game 21's plus the fixes after it (city targets, envoys, the settle advisor, the screenshot watermark). The fifth space project finished as turn 223 ended, and it was close: America and Spain had 4 of the 5 projects each. Sonnet won it as Opus did on the same start, a few turns later and for half the cost. On turn 204 it loaded its own turn-200 save and played turns 200 to 204 again, the first time an agent in this benchmark has gone back in time to undo a decision (below).

| | |
|---|---|
| Played | 2026-11-13 03:09 to 08:24 CET, 5.25 hours wall clock, about 10 minutes of it in one AI-turn hang (turn 130) |
| Turns | 223 (median 63 s per turn) |
| API-equivalent cost | **$34.13** at list prices (Sonnet 5.5: $2 / $10 per MTok in / out, $0.10 cache read, $4 cache write with the 1-hour TTL) |
| Tokens | 425K output, 240M cache read, 1.46M cache write, 2.5K uncached input |
| API requests | 1,248 (about 5.6 per turn) |
| Tool calls | 2,373, 3 returned an error (the tool's short name after a compaction, below) |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 4 times (turns 86, 134, 179 and 214) |

Cache reads are 70% of the bill ($24.03), cache writes 17% ($5.84) and output 12% ($4.25). By 50-turn range the game cost $2.62, $8.45, $9.77, $9.09 and $4.20 (turns 201 to 223, plus the closing summary). Turns 200 to 204 cost $2.33 in all, $1.44 the first time and $0.89 the second.

## Final standings (turn 223)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| America | **630** | **14** | 312 | **68** | **51** | 848 | 4 |
| Germany | 606 | 12 | 241 | 60 | 43 | 1,238 | 0 |
| Egypt | 605 | 13 | 150 | 47 | **51** | 506 | 0 |
| Rome | 474 | 11 | 144 | 55 | 45 | 796 | 0 |
| **Sumeria (Sonnet 5.5, winner)** | **471** | **10** | **387** | **68** | **33** | **707** | **4, then 5** |
| Spain | 429 | 5 | 203 | 63 | 50 | **1,264** | 4 |
| Greece | 349 | 6 | 199 | 60 | 35 | 346 | 1 |
| Brazil | 343 | 6 | 59 | 42 | 43 | 341 | 0 |

## How it went

The start was slow and full of barbarians: 2 cities at turn 15, 3 at turn 29 and 4 at turn 48, and from turn 30 to about turn 150 the agent fought barbarian scouts, warriors, archers, men-at-arms, crossbows and later musketmen and line infantry around Uruk, Nippur and Lagash, losing builders (it took some back), traders and an archer. At turn 50 it was last in score (72), with 10 techs to the best AI's 17, and had met no other civ; it met Brazil before turn 60 and Germany on turn 70. Unit upkeep held its gold income near 0 around turn 60. It had 7 cities by turn 86, 9 by turn 108 and 10 from turn 121, and kept all 10 to the end. At turn 100 it was 7th in score with 23 techs to the best AI's 33, but its science per turn (67) was already the highest of any civ, and it stayed first in science most turns from there on (94 at turn 123, 163 at turn 140, 186 at turn 150).

It made friends with Germany (turn 102), traded Horses and open borders with Spain for Tea (turn 100), and allied with Brazil (turn 134) and Spain. Egypt denounced it on turn 145 and Greece on turn 156, both far away. At turn 150 it was 4th in score with 41 techs to the best AI's 44, and had Rocketry: Uruk started a Spaceport that turn, and the agent saved its Great Scientist points for Carl Sagan, recruited on turn 160 and used on Uruk's first project. Rome declared war on turn 181 and sent a legion, line infantry and artillery at Isin; field cannon and city fire killed the legion and the artillery, Rome plundered one trader, and peace came on turn 190. No city fell.

The space race was close. America finished its first project on turn 175, Sonnet on turn 179 (Earth Satellite, with Sagan), and it built three spaceports in parallel (Uruk, then Lagash and Nippur, started on turns 174 and 178). Wernher von Braun cut the Moon Landing to 5 turns (second project, turn 196). Its third and fourth came on turns 209 and 214; America had 4 from turn 210 and Spain from turn 221. The agent sent spies at America's spaceports: Disrupt Rocketry succeeded at Charleston on turn 201, at Washington on turn 213 and at Charleston again on turn 219, and America finished no project after turn 210. Two spies were lost; on turn 218 the agent wrote "Spies appear to die when traveling to America; not worth more". Mars Hydroponics in Lagash finished as turn 223 ended, the fifth project. At the end Sonnet had the highest science (387 a turn, America 312) and was level with America in techs (68), but 5th in score.

### Turn 204: back to turn 200

On turn 201 Sonnet tried Democracy (not unlocked yet) and switched from Classical Republic to Communism, which it had just unlocked; its science fell from 309 to 226. On turn 203 it switched back to Classical Republic. The game then showed no government at all: science, culture and gold income at 0, and -133 gold a turn in upkeep. Three more switches and two policy changes did not bring the yields back, and gold fell from 807 to 224 (133 in upkeep, 450 for a policy change). On turn 204 it listed the saves, loaded its turn-200 save, from before the first switch, and played turns 200 to 204 again, this time without touching the government (its civic pick changed from Class Struggle to Professional Sports). The detour took 19 minutes and $2.33. In the replay it knew things it could not have known: "Farrah was already killed in this timeline at T202". It was not a bug. The base game puts a civ that goes back to a government it has had before into Anarchy, at least 3 turns with no gold, science, culture or faith, and its Government screen warns before the switch ("Having tried Classical Republic before, the people are wary of a return to this government"). civ6-mcp's `change_government` skipped that warning and the screen's other checks, answered `GOVERNMENT_CHANGED`, and its description said a switch after unlocking a new tier is free. Replayed from the turn-201 save, a switch to Oligarchy and back to Classical Republic on the same turn put the game into Anarchy until turn 204 the same way.

The load tools are there to recover a game that hung or crashed, and every earlier load in this benchmark was a same-turn or one-turn recovery. From game 23 the harness refuses a save from a turn earlier than the highest turn the run has reached (below).

## Sonnet 5.5 on Prince and King, Opus 5.5 and Fable 5.2 on King

| | Game 13 (Sonnet 5.5, Prince) | **Game 22 (Sonnet 5.5, King)** | Game 19 (Opus 5.5, King) | Game 17 (Fable 5.2, King) |
|---|---|---|---|---|
| Result | Science victory, turn 219 | **Science victory, turn 223** | Science victory, turn 218 | Science victory, turn 170 |
| Turn 50: score / cities / techs (best AI) | 72 / 4 / 10 (17) | **72 / 4 / 10 (17)** | 64 / 3 / 12 (15) | 74 / 4 / 13 (15) |
| Turn 100: score / cities / science / techs (best AI) | 176 / 8 / 65 / 23 (32) | **172 / 7 / 67 / 23 (33)** | 206 / 9 / 82 / 27 (35) | 238 / 8 / 101 / 31 (35) |
| Turn 150: score / cities / science / techs (best AI) | 315 / 13 / 148 / 34 (43) | **308 / 10 / 186 / 41 (44)** | 325 / 9 / 264 / 45 (45) | 396 / 8 / 317 / 57 (48) |
| Turn 200: score / science / techs (best AI) | 463 / 372 / 66 (55) | **432 / 309 / 61 (61)** | 443 / 235 / 67 (68) | (game over) |
| Its space projects (turn reached) | 1 (187) ... 5 (219) | **1 (179), 2 (196), 3 (209), 4 (214), 5 (223)** | 1 (165), 2 (188), 3 (211), 4 (214), 5 (218) | 1 (145), 2 (157), 3 (160), 4 (168), 5 (169) |
| Best AI's space projects at the end | 3 (Greece) | **4 (America, Spain)** | 4 (Greece, America) | 2 (Spain) |
| Cities lost | none | **none** | none | none |
| Final score and rank | 513, 2nd of 8 | **471, 5th of 8** | 470, 5th of 8 | 442, 1st of 8 |
| Cost (per turn) | $36.01 ($0.164) | **$34.13 ($0.153)** | $64.28 ($0.295) | $71.03 ($0.418) |
| Wall clock (median per turn) | 8.1 h (75 s) | **5.25 h (63 s)** | 6.4 h (68 s) | 5.3 h (88 s) |

Sonnet's King game started like its Prince game, to the number at turn 50 (72 score, 4 cities, 10 techs against 17), and was 10 techs behind at turn 100 on both. It caught up faster on King, with fewer cities and more science per turn (186 at turn 150, to 148 on Prince), and its space race ended within 5 turns of Opus's on the same start, with the same final score and rank and two AI civs one project short in both games. It cost about half as much as Opus ($0.15 a turn to $0.30) and less than a quarter of Fable 5.2, which won 53 turns sooner. Sonnet has now won all three of its games (Prince twice, King once).

## The harness in this game

From the server log, the run log and the agent's tool results:

- **One AI-turn hang** on turn 130: the end turn waited 594 s, civ6-mcp reloaded the turn's own save and ended the turn again. No stalled end turns otherwise.
- **The tool's short name after a compaction.** After three of its four compactions (turns 87, 179 and 214), Sonnet's first order call used `issue_orders` instead of the tool's full name, `mcp__civ6__issue_orders`. Claude Code answered "No such tool available" and the next call worked. These are the game's 3 tool errors.
- **The rewind on turn 204** (above). From game 23, `change_government` checks what the game's Government screen checks: it refuses a change on a turn with no completed civic, a second change in a turn and any change during Anarchy, warns before a switch that brings Anarchy (the same call again on the same turn confirms it), and says when Anarchy ends. From game 23, `load_game_save`, `load_save`, `load_save_from_menu` and `restart_and_load` refuse a save from a turn earlier than the highest turn the run has reached (`Error: EARLIER_TURN|...`); a save of the same turn, or of a later one, still loads. The highest turn is kept per run in a file on the game PC, so it outlives a restart of the server.
- **Spies in transit.** `get_spies` listed nothing while a spy travelled, so the agent saw spies vanish ("Spy list empty while spy in transit", turn 212) and new ids after each trip. Replayed on game 21's turn-126 save, `get_spies` showed none while the spy bought on turn 124 travelled to Sparta: a travelling spy is not among the player's units, so civ6-mcp cannot list it (it handles one it can see off the map). The spy-escape note added after game 21 says a spy may not show while it travels; listing travelling spies is still open.
- **Game 21's fixes, tested on its saves after this game:** on turn 40, a War-Cart's attack across a river now stops next to the target saying the game stopped it with 3 moves left, and the second attack comes back `NOT_ATTACKED` with the scout still at 100 HP, where game 21 got an estimate of a near kill. On turn 132 the end turn now says civ6-mcp picked the City Center as Sherzi's escape route.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 224 is the agent's closing summary after the victory screen. Rows 200 to 204 hold both passes of those turns.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city (turns 200 to 204 as replayed).
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 223 (game window on top, war room below).
