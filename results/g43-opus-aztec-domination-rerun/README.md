# Game 43: Opus 5.5 as the Aztecs on Prince, goal: Domination (game 28 without the leak)

**Result: Domination victory on turn 164, 1st of 8 in score (902 to India's 337).** Opus 5.5 (high effort) played the Aztecs (Montezuma) on Prince against the same seven AI civs as in game 28: Russia, Sumeria, India, Greece, America, China and England. Civ, level, map script, size, speed (Online, 250-turn limit) and seed are game 28's. Game 28 won on turn 122, but a fallback trade-route list had shown it the cities of every civ, all seven rival capitals among them, on turn 30, 15 to 40 turns before it met those civs. This game ran on the harness that no longer gives that list (from game 43, [setup](../../docs/setup.md)), and it won 42 turns later, at $20.80 more.

| | |
|---|---|
| Played | 2026-11-18 23:58 to 2026-11-19 07:54 CET, 7.9 hours wall clock |
| Turns | 164 (median 162 s per turn) |
| API-equivalent cost | **$78.37** at list prices, $0.48 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 579K output, 257M cache read, 1.9M cache write, 2.7K uncached input |
| API requests | 1,352 (about 8.2 per turn) |
| Tool calls | 1,919, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions. It compacted its context five times (turns 63, 96, 117, 137 and 154) |

Cache reads are 66% of the bill ($51.36), cache writes 20% ($15.41) and output 15% ($11.58). Turns got slower as the army grew: turns 1 to 50 cost $10.64 (median 73 s a turn), 51 to 100 $23.17 (163 s), 101 to 150 $33.80 (217 s) and 151 to the end $10.76 (299 s). The Aztecs had 13 military units on turn 50, 35 on turn 100 and 76 at the end.

## How it went

Opus's turn-1 plan: "Aztec domination goal. Start: wheat x3, salt, wine, copper. Plan: scout, warrior/eagle, settlers; find nearest neighbor for early eagle warrior pressure." It took City Patron Goddess as its pantheon (turn 35), never founded a religion, and moved from Chiefdom to Oligarchy (turn 44), Merchant Republic (92) and Fascism (148).

**A slower start than game 28.** Barbarian horsemen raided the capital from turn 26, killed an Eagle Warrior and took builders and the capital's new settler. The settler fell to a harness fault: an order to a Slinger Opus had upgraded the turn before moved the settler instead, out of the capital and next to a barbarian horseman (below). Opus's note: "Mistake: unit IDs shifted after upgrade; my settler got moved out of capital" (turn 27). The Aztecs took it back on turn 36, and it founded Teotihuacán on turn 39. On turn 50 the Aztecs had 4 cities and were 6th of 8 in score (64); game 28 had 8 cities and led (105).

| Turn | Rival capital taken |
|---|---|
| 52 | St. Petersburg (Russia) |
| 85 | Uruk (Sumeria) |
| 120 | Washington (America) |
| 150 | Delhi (India) |
| 155 | London (England) |
| 159 | Sparta (Greece) |
| 164 | Xi'an (China) |

**Russia and Sumeria.** Opus declared a surprise war on Russia on turn 43 and declared friendship with Sumeria the same turn. Eagle Warriors and archers took St. Petersburg on turn 52, and Russia paid 55 gold and 9 gold a turn for peace on turn 54. A second war (turns 70 to 81) took Moscow and Tver, for 10 gold a turn more. Opus then turned on its friend: war on Sumeria on turn 82, Uruk on 85 ("2/6 capitals", it wrote, with England not yet met), Nippur on 91, peace on 93.

**America and India.** War on America on turn 97 took Los Angeles (98), Boston (103), Baltimore (111) and Washington (120), and America paid 194 gold and 21 gold a turn for peace. Opus found Washington by elimination: on turn 100 it wrote "America 'holds own capital': Washington is not Boston? Probably the city at (46,30)." India came next, from turn 123: Patna (132), Chennai (141) and Delhi (150) with Field Cannons, Artillery and Napoleon as Great General. India offered peace with gold on turns 131, 135, 138 and 148 and was refused each time; Opus took its fifth offer, 269 gold and 77 gold a turn, the turn after Delhi fell.

**The last three.** England, met only on turn 126, was at war from turn 141; London fell on 155, and England paid 3 gold for peace. Greece (from turn 151) lost Athens on 153 and Sparta on 159. China (from 154) lost Changsha (156), Wuhan (163) and, on turn 164, Xi'an to three tanks, and the game ended on a Conquest victory, the game's own name for Domination. Opus's note that turn: "All 7 rival original capitals are now held ... Score 902 vs the next-best 337."

The Aztecs founded 15 cities and took 22, two of them city-states (Mogadishu and Mohenjo-Daro). Every rival civ still had at least two cities at the end; in game 28 four were out.

| Turn | Score (rank) | Cities | Rival capitals held | Techs (best AI) | Military (best AI) |
|---|---|---|---|---|---|
| 50 | 64 (6th) | 4 | 0 | 10 (14) | 300 (131) |
| 75 | 148 (2nd) | 9 | 1 | 18 (26) | 549 (337) |
| 100 | 360 (1st) | 20 | 2 | 30 (34) | 1,483 (611) |
| 125 | 516 (1st) | 24 | 3 | 38 (40) | 2,483 (476) |
| 150 | 675 (1st) | 29 | 4 | 50 (46) | 4,393 (330) |
| 164 | 902 (1st) | 37 | 7 | 57 (49) | 5,162 (256) |

## Final standings (turn 164)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| **Aztecs (Opus 5.5, winner)** | **902** | **37** | **313** | **57** | **39** | **5,162** |
| India | 337 | 7 | 107 | 49 | 31 | 222 |
| China | 320 | 6 | 43 | 36 | 34 | 121 |
| Greece | 272 | 6 | 98 | 41 | 25 | 166 |
| Russia | 174 | 3 | 20 | 28 | 26 | 122 |
| England | 166 | 2 | 20 | 33 | 19 | 134 |
| America | 146 | 3 | 11 | 31 | 23 | 256 |
| Sumeria | 135 | 3 | 20 | 27 | 20 | 16 |

## Against game 28

| | Game 28 (with the leak) | Game 43 (without) |
|---|---|---|
| Rival capitals known | All seven from turn 30, from the trade-route list | Each when its civ was met, or later |
| Civs met (turn) | Russia 25, America 45, India 61, Greece 63, England 64, China 68, Sumeria 70 | Russia 9, Sumeria 25, India 66, Greece 69, America 74, China 83, England 126 |
| Cities on turns 50 and 100 | 8 and 24 | 4 and 20 |
| Rival capitals taken (turn) | 50, 63, 74, 91, 96, 105, 122 | 52, 85, 120, 150, 155, 159, 164 |
| Result | Domination victory, turn 122 | Domination victory, turn 164 |
| AI civs out at the end | 4 | 0 |
| Cost and time | $57.57, 5.1 hours | $78.37, 7.9 hours |

The two games split before the leak could matter: here Russia was met on turn 9 instead of 25 and barbarians took a settler, and the Aztecs had half game 28's cities on turn 50. Both took Russia's capital around turn 50. The gap opened after that. Game 28 took the other six capitals in 72 turns, routing its army from one known capital to the next; game 43 took them in 112, and met England, the last civ, only on turn 126. One run each, so the 42 turns are the leak and the slower start together, not the leak alone. Game 43 also played with fixes game 28 lacked (from game 29 on): AI peace offers reached Opus instead of being closed as war declarations, and it took six of the sixteen, with 538 gold up front and 122 gold a turn in all.

## The harness in this game

From the run log and the agent's tool results and tooling notes:

- **An order moved the wrong unit (fixed after this game).** civ6-mcp finds a unit by the low part of its id, its slot (id % 65536, the `idx` that `get_units` shows), and never checked the rest. On turn 26 Opus upgraded Slinger 589829 (slot 5), which became Archer 851977, and the Settler the capital finished that turn took slot 5 as id 917509. On turn 27 Opus ordered 589829 to move to (36,16), and the Settler walked from the capital to (36,14), where barbarians took it. It was won back nine turns later. From game 44 every tool that takes a `unit_id` checks the whole id first and refuses one whose unit is gone, naming the unit now in its slot and, after an upgrade, the new id; `upgrade_unit` names the new id too ([setup](../../docs/setup.md)).
- **No unmet civ in the trade-route list.** All 10 `get_trade_destinations` answers named only civs the Aztecs had met that turn, checked against the game's per-turn contacts. The fix from game 43.
- **Policy prices.** On turn 94 a swap that would have cost 210 of 1,306 gold came back unpaid with the price and "Humanism completes in 2 turns", and Opus waited. Its other 11 `set_policies` calls came on turns a change was free. The fix from game 43.
- **Production refusals named the reason**: three in the game, two buildings already built and one Trader over the route capacity ("you have 9 Traders but only 9 trade route capacity"). The fix from game 43.
- **War declarations.** Opus declared all eight wars; no AI declared one. Three sends did not take effect (two on turn 43, one on 151); each time the tool said "DECLARE_SURPRISE_WAR did not take effect. Send it again", and a later send took. On the eight turns a war began no order was refused without a reason (the 19 refused were stacking and empty-tile errors), so game 42's war-turn refusals, which came on turns an AI declared war, did not come up.
- **Notes Opus left, not looked into yet.** A damaged Temple's repair could not be queued ("already built", turn 64), upgrade prices doubled from one turn to the next (turn 137, "horse→cav 190g, was 95g, cause unknown"), and units on multi-turn moves kept stopping the turn for orders (turns 139 to 158).
- No skipped turns, no AI-turn hangs, no tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 165 is the agent's closing reply after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 164 (game window on top, war room below).
