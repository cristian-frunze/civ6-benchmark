# Game 34: Opus 5.5 as Japan on Prince, goal: Domination victory

**Result: Domination victory on turn 236, 1st of 8 in score (988 to Brazil's 425).** Opus 5.5 (high effort) played Japan (Hojo Tokimune) against seven AI civs: Russia, Greece, Brazil, Germany, America, Egypt and Sumeria, the same rivals and start as India in game 33. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the earlier games. It is the fourth Domination game, after Sumeria (game 4, turn 169), Scythia (game 24, turn 149) and the Aztecs (game 28, turn 122), all wins. The harness was game 33's.

| | |
|---|---|
| Played | 2026-11-16 09:04 to 17:28 CET, 8.4 hours wall clock |
| Turns | 236 (median 109 s per turn) |
| API-equivalent cost | **$87.65** at list prices, $0.37 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 633K output, 297M cache read, 1.96M cache write, 3.0K uncached input |
| API requests | 1,514 (about 6.4 per turn) |
| Tool calls | 2,110, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions. It compacted its context 5 times (turns 96, 135, 169, 191 and 215) |

Cache reads are 68% of the bill ($59.33), cache writes 18% ($15.64) and output 14% ($12.66). Turns 1 to 50 cost $5.82 (median 48 s a turn), 51 to 100 $14.48 (67 s), 101 to 150 $20.06 (131 s), 151 to 200 $27.07 (180 s), and 201 to the end $20.22 (178 s).

## How it went

Opus's turn-1 plan: "Japan, goal Domination. Samurai via Feudalism civic. Meiji Restoration: cluster districts. Early plan: scout, settlers, expand to 4-6 cities, then military." The start was the one India had in game 33, cut off from most of the map: at turn 100 Japan had met only Russia and explored 13% of the land ("Domination requires finding 6 unmet capitals — need exploration"). It was 6th of 8 in score at turn 50 and 5th at turn 100, with the strongest army already (503 to Germany's 423).

From turn 93 it took the rivals one or two at a time, made peace with each when its capital fell, and took tribute in the peace deals:

| Turns | War | Cities taken (capital in bold) | Peace |
|---|---|---|---|
| 93-116 | Surprise war on Russia | **St. Petersburg** (112), Tula (115) | Turn 116: Marble, 13 gold and 2 gold a turn |
| 130-164 | Surprise war on Germany | Ulm (134), Nuremberg (140), Bremen (143), Heidelberg (151), **Aachen** (164) | Turn 164: a Great Work, 169 gold and 26 gold a turn |
| 167-178 | Surprise war on Brazil | Curitiba (170), **Rio de Janeiro** (174) | Turn 178: 53 gold a turn |
| 174-182 | Formal war on Sumeria | **Uruk** (182) | Turn 182: 39 gold |
| 183-194 | Formal war on Germany again | Augsburg (184), Mainz (189) | Turn 194: 236 gold and 48 gold a turn |
| 189-200 | Formal war on Egypt | Swenett (194), Akhetaten (197), **Râ-Kedet** (200) | Turn 200, Opus's own offer |
| 200-236 | Formal war on Greece, then America (from 225) | Pergamon (204), Megara (208), Athens (213), Argos (218), Mycenae (221), **Sparta** (225), Baltimore (230), Cincinnati (233), **Washington** (236) | Game over |

24 cities taken in all, every one kept; Japan ended with 33. Opus moved through the governments for war (Oligarchy on turn 51, Merchant Republic 103, Fascism 191), and its army peaked at 3,650 military strength at turn 200 against the best AI's 915. The late war strained the treasury: gold fell to -57 a turn, and on turn 209 Opus switched 9 rear cities to Commercial Hub and Campus projects and deleted 9 obsolete units. Rocket artillery broke the last walls; in Opus's closing summary, the worst losses came from "a coastal American submarine near Washington and from rockets left without infantry screening them". Washington fell on turn 236, the seventh capital.

| Turn | Score (rank) | Cities | Military (best AI) | Techs |
|---|---|---|---|---|
| 50 | 77 (6th) | 5 | 191 (161) | 13 |
| 100 | 193 (5th) | 7 | 503 (423) | 30 |
| 150 | 386 (1st) | 13 | 1,235 (583) | 49 |
| 200 | 691 (1st) | 24 | 3,650 (915) | 65 |
| 236 | 988 (1st) | 33 | 2,910 (726) | 68 |

## Final standings (turn 236)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| **Japan (Opus 5.5, winner)** | **988** | **33** | **346** | **68** | **48** | **2,910** |
| Brazil | 425 | 7 | 103 | 46 | 45 | 329 |
| Egypt | 418 | 10 | 107 | 47 | 51 | 726 |
| America | 403 | 7 | 68 | 45 | 46 | 433 |
| Russia | 325 | 9 | 133 | 48 | 33 | 0 |
| Sumeria | 321 | 8 | 103 | 54 | 40 | 46 |
| Greece | 276 | 3 | 42 | 63 | 36 | 26 |
| Germany | 220 | 3 | 34 | 42 | 30 | 86 |

## Four Domination games

| Game | Civ | Result | Capitals taken (first, last) | Cost | Hours |
|---|---|---|---|---|---|
| 4 | Sumeria | Domination victory, turn 169 | 7 (turns 42, 169) | $100.64 | 7.6 |
| 24 | Scythia | Domination victory, turn 149 | 7 (first by turn 44, last 149) | $82.02 | 7.1 |
| 28 | Aztec | Domination victory, turn 122 | 7 (turns 43, 122) | $57.57 | 5.1 |
| 34 | Japan | Domination victory, turn 236 | 7 (turns 112, 236) | $87.65 | 8.4 |

All four won. Japan's was the latest: its start met no civ but Russia for 100 turns, and the last two capitals sat across the map.

## The harness in this game

From the run log and the agent's tool results:

- **Rival capitals from the trade route list (found after game 41).** On turn 38 a Trader the game would send nowhere got civ6-mcp's fallback list instead of its destinations: every city of every civ not at war with Japan, 30 in all, among them those of seven civs it had not met. Opus wrote: "Rivals found via trade list: Russia St.Petersburg (39,40), Brazil (42,23), Germany (50,30, Heidelberg 44,35), Sumeria (34,17), Greece (57,14), Egypt (57-61,34), America (70,18)." `get_diplomacy` first listed them as met between turns 82 (Russia) and 195 (America), and the list came again on turn 143 with America and Greece still unmet. So this win knew where the rival capitals stood long before it met their civs. The harness gives no such list from game 43 ([setup](../../docs/setup.md)).
- **Every war declaration took.** Nine declarations, each confirmed by the war state read after it, and five peace offers from the AI civs reached Opus with their terms.
- **Embassies and delegations checked.** Egypt's, Sumeria's and Greece's embassies came back confirmed; Brazil's embassy (turn 144) and Germany's delegation (turn 113) came back `NOT_ACCEPTED`. A replay on game 33's turn-75 save showed such answers are real refusals: the AI's statement in the session is the game's `AI_REFUSE_DEAL`.
- **Moves that stopped short.** 319 results reported moves left instead of civ6-mcp's "moves exhausted", almost all 1 or 2 moves after one or two tiles, which fits a next tile costing more than the unit had left. None showed the full-allowance counts of game 33, where the read lagged; the fix for that came after this game. 72 blocked moves were explained from the game's facts.
- No AI-turn hangs, no tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 237 is the agent's closing summary after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150, 200 and 236 (game window on top, war room below).
