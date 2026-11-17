# Game 37: Opus 5.5 as Rome on Prince, goal: Domination victory

**Result: Domination victory on turn 176, 1st of 8 in score (953 to Brazil's 305).** Opus 5.5 (high effort) played Rome (Trajan) against seven AI civs: Russia, Germany, Brazil, Sumeria, Greece, Egypt and America. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the earlier games, and the leader changes the start and the rivals. It is the fifth Domination game: Sumeria won game 4 on turn 169, Scythia game 24 on turn 149, the Aztecs game 28 on turn 122 and Japan game 34 on turn 236. The harness had the fixes from games 35 and 36.

| | |
|---|---|
| Played | 2026-11-17 07:17 to 15:03 CET, 7.8 hours wall clock (a first start an hour earlier drew a Claude account whose login had expired; it was stopped on turn 1 before any turn was played, see [setup](../../docs/setup.md)) |
| Turns | 176 (median 117 s per turn) |
| API-equivalent cost | **$69.47** at list prices, $0.39 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 461K output, 237M cache read, 1.60M cache write, 2.5K uncached input |
| API requests | 1,255 (about 7.1 per turn) |
| Tool calls | 1,767, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions. It compacted its context 4 times (turns 72, 106, 141 and 163) |

Cache reads are 68% of the bill ($47.48), cache writes 18% ($12.77) and output 13% ($9.21). Turns 1 to 50 cost $7.44 (median 64 s a turn), 51 to 100 $22.51 (135 s), 101 to 150 $23.60 (132 s), and 151 to the end $15.93 (191 s).

## How it went

Opus's turn-1 plan: "Rome, Prince, Pangaea. Goal domination. Plan: expand to 4-6 cities, Iron Working for Legions, then conquer nearest capital." Rome led in score from turn 38 and had 6 cities at turn 50.

From turn 61 Opus fought one rival at a time: it declared a surprise war, turned down the AI's first peace offers until the capital had fallen, then accepted the next one, each with gold in it (Germany's second peace 80 gold and 25 a turn, Egypt's 282 gold and 128 a turn for 30 turns).

| Rival | War declared | Cities taken (turn) | Peace |
|---|---|---|---|
| Russia | 61 | St. Petersburg, the capital (72) | 72 |
| Germany | 73 | Cologne (78), Berlin, the capital (84) | 84 |
| Brazil | 90 | Rio de Janeiro, the capital (96) | 98 |
| Sumeria | 106 | Uruk, the capital (112) | 114 |
| Germany, again | 116 | Nuremberg (117), Aachen (123) | 124 |
| Greece | 127 | Knossos (165), Mycenae (168), Sparta, the capital (171), Corinth (172) | none |
| Egypt | 143 (a formal war) | Shedet (148), Akhetaten (154), Iwnw (157), Râ-Kedet, the capital (160) | 160 |
| America | 163 | Boston (174), Washington, the capital (176) | none (Opus turned down two offers) |

Rome also took the city-state Mogadishu on turn 139. Brazil declared war again on turn 168 and took nothing. Rome never lost a city. Its army moved from Legions and Battering Rams to Rocket Artillery, Modern Armor and Mechanized Infantry: by turn 150 Rome had 293 science a turn to the best AI's 96, and it ended with 66 techs (Future Tech) to the AI's best 48. Washington fell on turn 176 to one Rocket Artillery shot and three armored attacks, and with it Rome held all seven rival capitals.

| Turn | Score (rank) | Cities | Military (strongest AI) | Science / turn (best AI) |
|---|---|---|---|---|
| 50 | 101 (1st) | 6 | 315 (Egypt 117) | 26 (21) |
| 100 | 364 (1st) | 14 | 883 (Egypt 261) | 196 (65) |
| 150 | 698 (1st) | 19 | 1,444 (Greece 403) | 293 (96) |
| 176 | 953 (1st) | 28 | 2,636 (America 390) | 485 (57) |

## Final standings (turn 176)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| **Rome (Opus 5.5, winner)** | **953** | **28** | **485** | **66** | **46** | **2,636** |
| Brazil | 305 | 6 | 48 | 35 | 29 | 251 |
| Egypt | 290 | 5 | 38 | 42 | 40 | 0 |
| America | 282 | 7 | 49 | 34 | 27 | 390 |
| Greece | 217 | 3 | 11 | 48 | 28 | 20 |
| Russia | 212 | 5 | 57 | 30 | 19 | 9 |
| Germany | 179 | 3 | 30 | 36 | 22 | 26 |
| Sumeria | 161 | 5 | 52 | 29 | 20 | 106 |

## Five Domination games

| Game | Civ | Result | Capitals taken (first, last) | Cost | Hours |
|---|---|---|---|---|---|
| 4 | Sumeria | Domination victory, turn 169 | 7 (turns 42, 169) | $100.64 | 7.6 |
| 24 | Scythia | Domination victory, turn 149 | 7 (first by turn 44, last 149) | $82.02 | 7.1 |
| 28 | Aztec | Domination victory, turn 122 | 7 (turns 43, 122) | $57.57 | 5.1 |
| 34 | Japan | Domination victory, turn 236 | 7 (turns 112, 236) | $87.65 | 8.4 |
| 37 | Rome | Domination victory, turn 176 | 7 (turns 72, 176) | $69.47 | 7.8 |

All five won. Each civ had its own start and rivals, so the games compare loosely. Rome started its wars later than Sumeria, Scythia and the Aztecs (turn 61), took four capitals by turn 112, and the last three on turns 160 to 176.

## The harness in this game

From the run log and the agent's tool results and tooling notes:

- **War declarations that did not take.** On turn 90 two surprise-war declarations on Brazil came back `WAR_NOT_DECLARED` (the game still showed peace a few seconds later), a formal war was refused for lack of a denouncement, and a third surprise war took. The log does not show why the first two did not. Replayed after the game from the turn-90 save, with the same orders, the first declaration took. Open.
- **No order to rebase aircraft.** On turn 142 Opus found its air units could not move ("CANNOT_MOVE invalid state"): civ6-mcp has no rebase order, so an aircraft could only fight from the city that built it. Fixed after this game: `unit_action` has `rebase`, and a move sent to an aircraft is sent as one ([setup](../../docs/setup.md)).
- **The stacking check.** Opus reported on turns 107 and 118 that the move tool refused to put a Battering Ram on a tile with a combat unit, which the game allows: one unit of each formation class can share a tile, and a ram is a support unit, which civ6-mcp counted as a combat unit. Fixed after this game.
- **A ranged attack on a city** named the garrison unit as the target while the damage went to the walls (turn 169), and gave the damage dealt as the city's HP before the shot less the attacker's HP. Fixed after this game: the city is the target, and the damage dealt is what the city lost.
- **Turns that ended during a session.** 42 times a turn ended while Opus answered an AI civ (peace offers, deals, denunciations); each time the harness reported that the turn had ended and the next was open, as intended.
- **Moves that stopped short.** 74 results reported moves left instead of civ6-mcp's "moves exhausted", read from the game core.
- No AI-turn hangs, no tool errors and no outside action during the game. The National Park and wonder orders added for this game were not needed.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 177 is the agent's closing reply after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 176 (game window on top, war room below).
