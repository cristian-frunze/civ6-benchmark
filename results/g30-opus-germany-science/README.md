# Game 30: Opus 5.5 as Germany on Prince, goal: Science victory

**Result: Science victory on turn 213, 2nd of 8 in score.** Opus 5.5 (high effort) played Germany (Frederick Barbarossa) against seven AI civs: America, Greece, India, Egypt, Sumeria, Brazil and Russia. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the earlier games, and the leader changes the start and the rivals. Science is the goal Opus 5.5 won four times before on Prince, as Sumeria (games 3, 7, 8 and 10: turns 212, 206, 224 and 200). The harness was game 28's fixed one, the same as game 29's.

| | |
|---|---|
| Played | 2026-11-15 03:44 to 08:41 CET, 4.9 hours wall clock |
| Turns | 213 (median 62 s per turn) |
| API-equivalent cost | **$57.03** at list prices, $0.27 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 354K output, 203M cache read, 1.17M cache write, 2.2K uncached input |
| API requests | 1,098 (about 5.2 per turn) |
| Tool calls | 1,647, none returned an error |
| Claude Code sessions | 2. On turn 176 the first account reached its weekly limit, and the runner resumed the same session on another account within the turn. It compacted its context 3 times (turns 86, 152 and 192). No interventions |

Cache reads are 71% of the bill ($40.62), cache writes 16% ($9.33) and output 12% ($7.07). Turns 1 to 50 cost $7.29 (median 49 s a turn), 51 to 100 $13.58 (59 s), 101 to 150 $15.95 (56 s), 151 to 200 $18.05 (106 s), and 201 to the end $2.15 (51 s).

## How it went

Opus's turn-1 plan: "Germany, science victory plan. Need expansion to 6+ cities, campuses, Hansa IZs." Barbarians from a camp west of Aachen took a builder and kept the first 50 turns slow: 3 cities and last of 8 in score at turn 50. Then it settled fast, to 9 cities by turn 91, and led in score at turn 100.

Two AI civs declared war on Germany and took nothing. Greece and its city-states came on turn 102 with five knights at Trier. Opus bought walls, killed the knights with city and crossbow fire, lost one crossbowman, and Greece accepted its peace offer on turn 112. America declared war on turn 155 and attacked Magdeburg with knights and field cannon. Opus bought anti-tank crews, rerouted its traders, and on turn 162 accepted America's own peace offer, which added a Great Work and 24 gold. Opus never declared a war.

The space race:

| Turn | Event |
|---|---|
| 173 | Launch Earth Satellite (Germany's 1st project) |
| 185-186 | Spaceports in Frankfurt and Mainz, after Aachen's |
| 187 | Moon Landing (2nd) |
| 188-206 | Greece 2 projects, America 2, Sumeria 1 |
| 201 | Mars Habitation in Aachen (3rd) |
| 204 | Mars Hydroponics in Frankfurt (4th) |
| 213 | Mars Reactor in Aachen (5th): Science victory |

To speed up the last project, Opus built an Encampment in Aachen and bought its Barracks, Armory and Military Academy for the Integrated Space Cell policy (+15% to space projects there), sent trade routes from every other city into Aachen, and bought Power Plants in Frankfurt and Mainz. Spies ran counterspy missions on Aachen's Spaceport and Disrupt Rocketry on Washington's, and two were lost. America was the other threat, on culture: 121 of the 137 visiting tourists it needed at turn 210.

| Turn | Score (rank) | Cities | Techs (best AI) | Science / turn (best AI) | Military (best AI) |
|---|---|---|---|---|---|
| 50 | 60 (8th) | 3 | 10 (14) | 12 (26) | 184 (240) |
| 100 | 218 (1st) | 9 | 28 (29) | 83 (69) | 263 (409) |
| 150 | 379 (2nd) | 9 | 45 (45) | 186 (155) | 450 (800) |
| 200 | 516 (2nd) | 9 | 67 (59) | 276 (295) | 1,455 (758) |
| 212 | 540 (2nd) | 9 | 68 (63) | 314 (279) | 1,669 (1,151) |

## Final standings (turn 212, the last diary row)

| Civ | Score | Cities | Science / turn | Techs | Military | Tourism / turn | Space projects |
|---|---|---|---|---|---|---|---|
| America | 572 | 13 | 279 | 63 | 609 | 240 | 2 |
| **Germany (Opus 5.5, winner)** | **540** | **9** | **314** | **68** | **1,669** | **368** | **4, the 5th on turn 213** |
| Greece | 468 | 11 | 204 | 59 | 135 | 252 | 2 |
| India | 454 | 10 | 149 | 60 | 294 | 248 | 0 |
| Egypt | 450 | 11 | 108 | 49 | 1,151 | 434 | 0 |
| Sumeria | 359 | 9 | 173 | 57 | 273 | 116 | 1 |
| Brazil | 318 | 5 | 67 | 40 | 193 | 101 | 0 |
| Russia | 247 | 4 | 59 | 34 | 67 | 20 | 0 |

## Opus 5.5's Science wins on Prince

| Game | Civ | Result | Cost | Hours |
|---|---|---|---|---|
| 3 | Sumeria | Science victory, turn 212 | $56.43 | |
| 7 | Sumeria | Science victory, turn 206 | $62.87 | |
| 10 | Sumeria | Science victory, turn 200 | $58.24 | 5.5 |
| 30 | Germany | Science victory, turn 213 | $57.03 | 4.9 |

Game 8 (Sumeria, medium effort) won on turn 224. Game 30 has another start and other rivals, so the turn is not directly comparable, but it lands in the same range at the same cost. Germany started slower than Sumeria in games 3, 7 and 10 (3 cities and 10 techs at turn 50, to their 4 or 5 and 11 to 14), was level with them by turn 100 (28 techs to their 26 to 31) and matched game 10 at turn 200 (67 techs; games 3 and 7: 63 and 65).

## The harness in this game

From the run log and the agent's tool results:

- **Game 28's peace fix ran as intended.** America's peace offer on turn 162 reached Opus as a deal with its terms (a peace treaty, a Great Work and 24 gold), and Opus accepted it.
- **One AI-turn hang** after turn 174, about 15 minutes: the runner reloaded the turn's start save and ended the turn again, and told Opus what was undone. Opus replayed the turn.
- **A weekly usage limit on turn 176.** The runner resumed the same session on another account, and the turn went on.
- **Archers refused as "LOS blocked or unit already attacked this turn"** 14 times, mostly turns 36 to 67. None had attacked earlier that turn, so it was line of sight each time, but the message left Opus guessing ("maybe tool LOS check is off", turn 42). The game's own reason is not passed on yet.
- **Other notes not looked into yet.** A Trader refused as `CANNOT_START` with no reason (turn 127, as in games 28 and 29), and a travelling spy missing from `get_spies` (turn 200).
- No tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 213 is the agent's closing summary after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150, 200 and 213 (game window on top, war room below).
