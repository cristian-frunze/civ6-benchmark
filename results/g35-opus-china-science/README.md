# Game 35: Opus 5.5 as China on Prince, goal: Science victory

**Result: Science victory on turn 166, 1st of 8 in score (540 to India's 403).** Opus 5.5 (high effort) played China (Qin Shi Huang) against seven AI civs: India, England, Russia, America, Sumeria, Brazil and Greece. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the earlier games, and the leader changes the start and the rivals. It is the earliest Science win by Opus in these games: Sumeria won on turns 200 to 224 (games 3, 7, 8 and 10), Germany on turn 213 (game 30), and the one-Opus hotseat game (h2) on turn 168. The harness was game 34's plus the fix that reads a stopped unit's moves from the game core.

| | |
|---|---|
| Played | 2026-11-16 17:54 to 22:47 CET, 4.9 hours wall clock |
| Turns | 166 (median 82 s per turn) |
| API-equivalent cost | **$52.41** at list prices, $0.32 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 300K output, 189M cache read, 1.06M cache write, 2.0K uncached input |
| API requests | 1,018 (about 6.1 per turn) |
| Tool calls | 1,326, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions. It compacted its context 3 times (turns 73, 119 and 163) |

Cache reads are 72% of the bill ($37.90), cache writes 16% ($8.51) and output 11% ($6.00). Turns 1 to 50 cost $8.74 (median 60 s a turn), 51 to 100 $18.34 (83 s), 101 to 150 $20.70 (105 s), and 151 to the end $4.60 (116 s).

## How it went

Opus's turn-1 plan: "China: builders +1 charge, can rush ancient/classical wonders with charges; eurekas stronger. Goal Science victory. Plan wide expansion + campuses." It took Divine Spark as its pantheon (turn 11) and Classical Republic as its government (turn 33).

Greece was its neighbour. On turn 46 Opus declared a surprise war and took Pharsalos on turn 50, then found Sparta too strong ("hoplite garrison on hills") and made peace on turn 61, keeping the city. At turn 50 China had 7 cities and was 2nd in score (102 to Greece's 106).

On turn 61 Opus placed the Great Library next to Xi'an and planned to rush it with builder charges, China's ability. The harness had no order for that (below), so on turn 64 it moved Xi'an on to a Settler. On turn 81 it tried to resume the wonder and the game took none of its tiles; India finished the Great Library around turn 83. China's other wonders came later: Oxford University (turn 104) and the Forbidden City (turn 128, finished with the Great Engineer Gustave Eiffel).

From there the game was a science build: Campuses in every city, 18 great people recruited (Galileo, Emilie du Chatelet and Stephanie Kwolek among them), Merchant Republic from turn 98, and trade routes and luxury sales to keep the gold up. China led in score from turn 51 on and had 12 cities at turn 100, with 123 science a turn to India's 75. India and Russia declared war on turn 117 and made peace on turn 125; Greece and Brazil declared war on turn 139 and made peace on turn 148. China lost no city: it had 13 from turn 105 to the end.

Xi'an started a Spaceport on turn 110, Guangzhou on 113 and Taiyuan on 129. Opus built all five space projects one after another in Xi'an: the Earth Satellite from turn 133, the Moon Landing from 141, Mars Hydroponics from 149, Mars Habitation from 153 and the Mars Reactor from 163. The other cities ran Campus and Industrial Zone projects. With the Reactor about 7 turns out, Opus sold Incense, Oil, Citrus and Truffles to America, bought the Great Engineer Sergei Korolev for 3,335 gold on turn 165, and used him on Xi'an's Spaceport the next turn. His production finished the Reactor at once. No AI civ built a Spaceport.

| Turn | Score (rank) | Cities | Science / turn (best AI) | Techs (best AI) | Military (best AI) |
|---|---|---|---|---|---|
| 50 | 102 (2nd) | 7 | 24 (Greece 29) | 13 (15) | 320 (152) |
| 100 | 326 (1st) | 12 | 123 (India 75) | 38 (32) | 451 (513) |
| 150 | 501 (1st) | 13 | 259 (India 109) | 58 (44) | 974 (525) |
| 166 | 540 (1st) | 13 | 282 (England 116) | 63 (47) | 869 (676) |

## Final standings (turn 166)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| **China (Opus 5.5, winner)** | **540** | **13** | **282** | **63** | **34** | **869** |
| India | 403 | 8 | 108 | 47 | 35 | 335 |
| England | 346 | 9 | 116 | 39 | 24 | 676 |
| Russia | 315 | 7 | 61 | 35 | 28 | 321 |
| America | 304 | 6 | 51 | 37 | 34 | 265 |
| Sumeria | 252 | 7 | 96 | 39 | 28 | 193 |
| Brazil | 247 | 6 | 48 | 33 | 26 | 350 |
| Greece | 240 | 7 | 72 | 38 | 24 | 316 |

## Opus 5.5 Science games on Prince

| Game | Civ | Result | Cost | Hours |
|---|---|---|---|---|
| 3 | Sumeria | Science victory, turn 212 | $56.43 | 4.6 |
| 7 | Sumeria (game 3 repeated) | Science victory, turn 206 | $62.87 | 6.6 |
| 8 | Sumeria, medium effort | Science victory, turn 224 | $54.83 | 8.6 |
| 10 | Sumeria, fixed harness | Science victory, turn 200 | $58.24 | 5.5 |
| 30 | Germany | Science victory, turn 213 | $57.03 | 4.9 |
| 35 | China | Science victory, turn 166 | $52.41 | 4.9 |

China's start and rivals differ from Sumeria's and Germany's, so the games compare loosely. China won 34 turns before any other of them, at about the same cost, and close to Fable 5.2's Prince wins (turns 170 and 168, games 12 and 14).

## The harness in this game

From the run log and the agent's tool results:

- **China's builder charges could not reach the Great Library.** On turn 64 Opus tried three orders with its builder on the wonder's tile: `activate` answered "charges=0. No valid activation tiles found", `sacrifice_charges` asked for a Royal Society, and `improve` said the wonder was "not in game database". civ6-mcp has no order for the ability. Resuming the placed wonder on turn 81 also failed: without a tile `set_city_production` asked for one, with the tile it reported `SILENT_FAILURE`, and the wonder advisor then found no valid tiles. Both are to be fixed after game 36.
- **Diplomacy answers checked.** The embassies with Sumeria and England and America's delegation came back confirmed; delegations to India, Greece and Russia, Brazil's embassy and two friendships with America came back `NOT_ACCEPTED`.
- **Moves that stopped short.** 79 results reported moves left instead of civ6-mcp's "moves exhausted", 75 of them 1 move and 4 of them 2, with the moves now read from the game core. None showed a full allowance, the error game 33 had.
- **One AI-turn hang** (turn 141): the harness reloaded the turn's save and ended it again.
- No tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 167 is the agent's closing reply after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 166 (game window on top, war room below).
