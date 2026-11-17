# Game 38: Opus 5.5 as Spain on Prince, goal: Religious victory

**Result: Religious victory on turn 161, 2nd of 8 in score (362 to Brazil's 368).** Opus 5.5 (high effort) played Spain (Philip II) against seven AI civs: Rome, Greece, Brazil, Germany, America, Egypt and Sumeria. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the earlier games, and the leader changes the start and the rivals. It is the fifth Religious game and the fourth civ on that goal: Arabia won game 25 on turn 159, Russia lost games 29 and 31, and India won game 33 on turn 241. The harness had the fixes from games 35 to 37 (not the three found in game 37, which were deployed after this game).

| | |
|---|---|
| Played | 2026-11-17 15:03 to 20:46 CET, 5.7 hours wall clock (the first turn started at 15:12, after the run waited 9 minutes for a free Claude session slot) |
| Turns | 161 (median 84 s per turn) |
| API-equivalent cost | **$53.54** at list prices, $0.33 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 380K output, 177M cache read, 1.31M cache write, 1.9K uncached input |
| API requests | 955 (about 5.9 per turn) |
| Tool calls | 1,344, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions. It compacted its context 3 times (turns 86, 125 and 147) |

Cache reads are 66% of the bill ($35.43), cache writes 20% ($10.49) and output 14% ($7.60). Turns 1 to 50 cost $6.82 (median 49 s a turn), 51 to 100 $15.50 (85 s), 101 to 150 $24.07 (182 s), and 151 to the end $7.15 (188 s).

## How it went

Opus's turn-1 plan: "Spain, religious victory goal. Plan: Astrology first, then an early Holy Site to compete for a Great Prophet. Expand to 4-6 cities." It took Divine Spark as its pantheon on turn 21 and founded Catholicism on turn 33 (Feed the World and Pilgrimage), while Sumeria's Buddhism and Egypt's Judaism were the other early religions. With the Evangelize Belief order it added Holy Order on turn 70 and Mosque on turn 96, and it moved from Classical Republic (turn 44) to Monarchy (78) and Theocracy (93).

Spain fought no war in this game; each of the four earlier Religious games had one. Opus kept the neighbours friendly instead. Sumeria (turn 99), Rome (105) and Brazil (158) proposed alliances, which it accepted, and it renewed the alliances with Rome and Sumeria when they expired. Greece (turn 116), America (128) and Egypt (146) denounced Spain; none declared war.

Spain bought 48 Apostles and 17 Missionaries over the game, the first Apostle on turn 91, and built more Missionaries in Toledo. Egypt's Judaism was the race to beat: it held the majority in 4 of 8 civs from turn 106 to 129, while Catholicism held it in Spain alone until about turn 115. Then the Apostles turned Rome, Brazil, America and Sumeria: Catholicism had 3 of 8 by turn 125, 5 by turn 145 and 6 by turn 154. From turn 148 the Apostles fought Egypt's Inquisitors and Gurus around Râ-Kedet and Sais (9 theological attacks, 2 kills), and the spreads that followed turned Egypt. Germany came last: its cities were behind Greece in the far northeast, and Opus learned Aachen and Trier existed from Germany's trade screen (`get_trade_options`). Two spreads at Aachen, Germany's capital, on turn 161 gave Catholicism the majority in all 8 civs, and Spain won.

| Turn | Score (rank) | Cities | Cities following Catholicism | Faith / turn | Civs with a Catholic majority | Military (best AI) |
|---|---|---|---|---|---|---|
| 50 | 91 (3rd) | 5 | 3 | 10 | 1 of 8 (Spain) | 111 (186) |
| 100 | 227 (1st) | 8 | 12 | 71 | 1 of 8 | 347 (378) |
| 150 | 349 (1st) | 10 | 40 | 285 | 5 of 8 | 537 (675) |
| 161 | 362 (2nd) | 10 | 48 | 295 | 8 of 8 | 579 (511) |

## Final standings (turn 161)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| Brazil | 368 | 9 | 72 | 37 | 31 | 263 |
| **Spain (Opus 5.5, winner)** | **362** | **10** | **118** | **45** | **29** | **579** |
| Egypt | 359 | 7 | 59 | 37 | 43 | 511 |
| America | 354 | 9 | 252 | 53 | 30 | 310 |
| Greece | 294 | 7 | 86 | 35 | 28 | 100 |
| Rome | 242 | 7 | 115 | 34 | 23 | 325 |
| Sumeria | 200 | 5 | 50 | 31 | 21 | 249 |
| Germany | 190 | 3 | 16 | 29 | 26 | 362 |

## Five Religious games

| Game | Civ | Result | Religious units bought | Theological attacks (kills) | Wars | Cost | Hours |
|---|---|---|---|---|---|---|---|
| 25 | Arabia | Religious victory, turn 159 | 39 Apostles, 13 Missionaries | 0 (the harness had no theological combat yet) | yes | $50.03 | 5.0 |
| 29 | Russia | Defeat (Egypt, Culture), turn 224; Orthodoxy majority in 6 of 8 | 56 Apostles, 9 Missionaries | 0 | yes | $90.88 | 9.0 |
| 31 | Russia, fixed harness | Defeat (Greece, Science), turn 223; majority in 4 of 8 | 54 Apostles, 2 Missionaries | 17 (6) | yes | $84.74 | 6.9 |
| 33 | India | Religious victory, turn 241 | 63 Apostles, 16 Missionaries, 1 Guru | 13 (6) | yes | $95.39 | 9.0 |
| 38 | Spain | Religious victory, turn 161 | 48 Apostles, 17 Missionaries | 9 (2) | none | $53.54 | 5.7 |

Each civ had its own start and rivals, so the games compare loosely. Spain's win came 80 turns before India's and cost $42 less, with no war.

## The harness in this game

From the run log and the agent's tool results and tooling notes:

- **Alliance proposals reported as refused.** Opus proposed alliances four times. `form_alliance` answered `REJECTED` three times (Rome on turns 126 and 148, Sumeria on turn 142) and "status unclear" once (Sumeria, turn 121), yet each one became an alliance: `get_diplomacy` showed that civ as allied within minutes, and the diary rows show the alliance in force by the end of the turn (turn 128 for the first). civ6-mcp reads the AI's answer in the same frame it sends the deal, before the AI has answered, as it did for trades (fixed earlier). Fixed after this game ([setup](../../docs/setup.md)).
- **A turn that was skipped.** On turn 126 Rome's friendship offer paused the end of the turn; Opus answered it and proposed the alliance, and its next `end_turn` reported "Turn 126 -> 128". Turn 127 ended without any orders from Opus ("T127 was auto-skipped during the Rome diplomacy", its note on turn 128). It is the only skipped turn in games 36 to 38; the log does not show what ended turn 127. Open.
- **Diplomacy answers checked.** Friendships with Brazil (turns 85 and 139), Rome (99) and Sumeria (99, 120 and 142) came back confirmed; delegations to Brazil (turn 68), Sumeria and Rome (87), Egypt (99) and America (106), and four later friendships, came back `NOT_ACCEPTED`.
- **Evangelize Belief** was used twice (Holy Order on turn 70, Mosque on turn 96). The first try, on turn 69, was refused with the unit's 0 moves named: a promotion had ended the Apostle's turn.
- **Spread charges.** Opus noted three times (turns 40, 95 and 150) that `spread_religion` reported one charge more than the unit had left. To check.
- **Moves that stopped short.** 244 results reported moves left instead of civ6-mcp's "moves exhausted", read from the game core.
- No AI-turn hangs, no tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 162 is the agent's closing reply after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 161 (game window on top, war room below).
