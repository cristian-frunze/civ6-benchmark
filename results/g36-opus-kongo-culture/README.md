# Game 36: Opus 5.5 as Kongo on Prince, goal: Culture victory

**Result: Culture victory on turn 203, 2nd of 8 in score (698 to Egypt's 717).** Opus 5.5 (high effort) played Kongo (Mvemba a Nzinga) against seven AI civs: Egypt, Greece, Germany, Brazil, Russia, Sumeria and America. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the earlier games, and the leader changes the start and the rivals. It is the fourth Culture game: France lost game 26 and won game 27 on turn 195, and Greece won game 32 on turn 153. Kongo cannot found a religion and gets more from Great Works, relics and artifacts. The harness was game 35's.

| | |
|---|---|
| Played | 2026-11-16 23:04 to 2026-11-17 05:38 CET, 6.6 hours wall clock (the run waited 16 minutes before that for a free Claude session slot) |
| Turns | 203 (median 82 s per turn) |
| API-equivalent cost | **$63.02** at list prices, $0.31 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 374K output, 217M cache read, 1.51M cache write, 2.3K uncached input |
| API requests | 1,160 (about 5.7 per turn) |
| Tool calls | 1,695, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions. It compacted its context 4 times (turns 77, 121, 156 and 188) |

Cache reads are 69% of the bill ($43.45), cache writes 19% ($12.08) and output 12% ($7.48). Turns 1 to 50 cost $8.47 (median 58 s a turn), 51 to 100 $16.49 (96 s), 101 to 150 $18.38 (120 s), and 151 to the end $19.63 (87 s).

## How it went

Opus's turn-1 plan: "Kongo: Nkisi gives yields from relics/artifacts/sculptures, +50% great artist/writer/musician/merchant points; Mbanza unique district (Guilds). Cannot build holy sites/found religion in base game. Culture victory path: Theater Squares, Great Works, wonders." A barbarian archer captured a Settler on turn 36 and a warrior took a captured Settler back from barbarians on turn 40; Kongo was 3rd of 8 in score at turn 50 with 5 cities.

Russia and Greece declared war on turn 66 and made peace on turn 91 without taking a city; Opus switched to Merchant Republic the same turn. From there the culture grew fast: Theater Squares and Mbanzas in most cities, 7 wonders (Chichen Itza on turn 93, the Bolshoi Theatre 108, the Hermitage 132, the Colosseum 139, Broadway 159, Mont St. Michel 166 and the Forbidden City 168), and Great Writers, Artists and Musicians filling the slots, with Heritage Tourism in a policy slot from turn 108. Kongo led in score from turn 100 with 171 culture a turn to Egypt's 96. Its free Apostles came from Kongo's leader ability, and Opus promoted one to Martyr, so that its death in theological combat would give a relic.

Russia declared war on turn 140 and America on turn 143; they made peace on turns 149 and 150, paying Kongo a little gold (Russia 16 gold and 1 a turn, America 10). Kwila's Amphitheater and Artifact Museum were pillaged, and Opus repaired them. Opus's closing summary says "We were never at war", which is wrong: it fought both wars from its cities, and took nothing and lost nothing.

The race was with Egypt, which took Washington and most of America (it ended with 18 cities, America with 1) and had the most domestic tourists of the AI civs. From turn 150 Kongo had more than twice Egypt's tourism (536 to 205), but visiting tourists had to pass Egypt's domestic ones, and at turn 190 the gap was 30. Opus bought the Great Merchant Jamsetji Tata for 1,150 gold on turn 191, whose ability gives every Campus +10 tourism, then queued a Campus in every city that lacked one and bought Builders (about 2,100 gold) to chop forest and jungle for them: 3 Campuses on turn 191, 7 by turn 202. At the start of turn 203 Kongo had 269 visiting tourists against Egypt's 269 domestic, one short, and won as that turn ended. Opus turned down every AI request for its Great Works, the last Egypt's for three on turn 199.

| Turn | Score (rank) | Cities | Culture / turn (best AI) | Tourism (best AI) | Great Works | Wonders |
|---|---|---|---|---|---|---|
| 50 | 90 (3rd) | 5 | 14 (Egypt 19) | 0 (Egypt 11) | 0 | 0 |
| 100 | 285 (1st) | 10 | 171 (Egypt 96) | 42 (Egypt 48) | 12 | 1 |
| 150 | 508 (1st) | 12 | 380 (Egypt 270) | 536 (Egypt 205) | 46 | 4 |
| 200 | 684 (2nd) | 13 | 625 (Egypt 313) | 736 (Egypt 287) | 71 | 7 |
| 203 | 698 (2nd) | 13 | 646 (Egypt 294) | 756 (Egypt 287) | 71 | 7 |

## Final standings (turn 203)

| Civ | Score | Cities | Culture / turn | Tourism | Great Works | Wonders | Techs | Civics | Military |
|---|---|---|---|---|---|---|---|---|---|
| Egypt | 717 | 18 | 294 | 287 | 38 | 5 | 49 | 51 | 1,157 |
| **Kongo (Opus 5.5, winner)** | **698** | **13** | **646** | **756** | **71** | **7** | **57** | **51** | **701** |
| Greece | 405 | 9 | 64 | 90 | 0 | 4 | 49 | 31 | 1,049 |
| Germany | 398 | 8 | 152 | 116 | 15 | 1 | 41 | 35 | 1,042 |
| Brazil | 381 | 8 | 70 | 88 | 0 | 3 | 53 | 25 | 586 |
| Russia | 337 | 10 | 43 | 13 | 0 | 1 | 40 | 29 | 0 |
| Sumeria | 193 | 4 | 23 | 14 | 0 | 1 | 34 | 22 | 10 |
| America | 125 | 1 | 12 | 0 | 0 | 0 | 34 | 23 | 5 |

## Four Culture games

| Game | Civ | Result | Cost | Hours |
|---|---|---|---|---|
| 26 | France | Defeat (Greece, Science), turn 242; 227 of the 310 visiting tourists needed | $65.96 | 5.6 |
| 27 | France (game 26 on the fixed harness) | Culture victory, turn 195 | $51.28 | 4.6 |
| 32 | Greece | Culture victory, turn 153 | $43.09 | 3.9 |
| 36 | Kongo | Culture victory, turn 203 | $63.02 | 6.6 |

Each civ had its own start and rivals, so the games compare loosely. Kongo's was the closest finish: Egypt, the score leader, had the most domestic tourists of any AI civ, and Kongo passed them by one.

## The harness in this game

From the run log and the agent's tool results:

- **No National Park.** Opus bought a Naturalist on turn 163, and its `activate` came back "No valid activation tiles found" five times on turns 164 to 168, with "charges=0" and no tiles or reasons. A National Park needs four tiles of high enough appeal, and civ6-mcp has no order for it and shows no appeal, so the agent could not tell whether a park was possible anywhere. A Beach Resort was refused for "unknown reason" on turn 171 (Opus guessed low appeal). Both are on the list of open harness items.
- **Diplomacy answers checked.** Friendships with Egypt (twice), Germany and Russia and Brazil's embassy came back confirmed; delegations to America, Egypt and Greece, Sumeria's embassy and nine later friendships came back `NOT_ACCEPTED`.
- **Moves that stopped short.** 51 results reported moves left instead of civ6-mcp's "moves exhausted" (48 with 1 move, 3 with 2), read from the game core.
- **A turn that ended during a session.** On turn 141 Brazil's denunciation opened as the turn ended; the harness reported that turn 141 had ended while Opus answered and that turn 142 was open, as intended.
- No AI-turn hangs, no tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 204 is the agent's closing reply after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150, 200 and 203 (game window on top, war room below).
