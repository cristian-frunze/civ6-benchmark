# Game 28: Opus 5.5 as the Aztecs on Prince, goal: Domination victory

**Result: Domination victory on turn 122, 1st of 8 in score.** Opus 5.5 (high effort) played the Aztecs (Montezuma) against seven AI civs: Russia, America, Sumeria, China, India, Greece and England. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the earlier games. The leader is new, so the start and the AI civs changed. The harness was game 27's: the excavate order, the game's culture count, and the refusal reasons. It is the benchmark's third Domination win and the fastest. Game 24 (Scythia) won on turn 149 and game 4 (Sumeria) on turn 169. Game 28 won 27 turns sooner than game 24 and cost $24.45 less.

| | |
|---|---|
| Played | 2026-11-14 12:38 to 17:45 CET, 5.11 hours wall clock |
| Turns | 122 (median 127 s per turn) |
| API-equivalent cost | **$57.57** at list prices, $0.47 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 373K output, 201M cache read, 1.23M cache write, 2.2K uncached input |
| API requests | 1,081 (about 8.9 per turn) |
| Tool calls | 1,436, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions. It compacted its context 3 times (turns 64, 90 and 109) |

Cache reads are 70% of the bill ($40.25), cache writes 17% ($9.85) and output 13% ($7.46). Turns got slower and more expensive as the army grew. Turns 1 to 50 cost $10.22 (median 60 s a turn), 51 to 100 cost $31.76 (174 s), and 101 to 122 cost $15.59 (211 s). The Aztecs had 14 military units at turn 50, 32 at turn 100 and 47 at the end, with 88 units in all.

## How it went

| Turn | Original capital taken |
|---|---|
| 43 | Moscow (Russia, out on turn 50 when St Petersburg fell) |
| 63 | Washington (America, out on turn 80 when Boston fell) |
| 74 | Uruk (Sumeria, out) |
| 91 | Delhi (India) |
| 96 | Sparta (Greece) |
| 105 | Xi'an (China, out) |
| 122 | London (England) |

On turn 1 Opus wrote the plan it then followed: "Aztec domination plan: early expansion (4-6 cities), Eagle Warriors to capture builders, then Bronze/Iron for swords; target nearest civ capital once found." It settled six cities and declared a surprise war on Russia on turn 41. Two Eagle Warriors took Moscow on turn 43 and St Petersburg on turn 50, and Russia was out. The Aztecs had 8 cities at turn 50 and were 1st in score from turn 48 to the end.

America came next. War on turn 55, Philadelphia on turn 57, Washington on turn 63. America then offered 13 gold a turn for peace. Opus took it ("Boston isn't a capital, so I'll take the money and redirect the army toward Sumeria"). Uruk fell on turn 74, and Sumeria was out. On turn 78 Opus declared war on America again to clear the way to Delhi, and took Boston on turn 80. At turn 100 the Aztecs had 24 cities, 523 points to India's 215, 35 techs to the best AI's 30, and a military of 1,402 to the best AI's 157 (England).

From turn 84 Opus fought on three fronts. It declared war on China and took Shenyang (turn 86) and Beijing (87). India declared war on turn 85. Knights, crossbows and rams, with the Great General Boudica, took Delhi on turn 91. That turn Opus declared a surprise war on Greece, and Sparta fell on turn 96. China's capital turned out to be Xi'an, far east (70,18). A trebuchet broke its walls on turn 104, and cavalry took it on turn 105, which put China out. Opus made peace with Greece the same turn, and India refused.

England was last. War on turn 106, then Bradford on turn 111, then a siege of London (25,29) with field cannons and artillery. On turn 122 an artillery piece and three field cannons took London's walls and garrison to zero, and a knight took the city. The game ended that turn on a Conquest victory, the game's own name for Domination. The Aztecs then had 29 cities, 330 science a turn to Greece's 63, and 47 techs to the best AI's 34.

| Turn | Score (rank) | Cities | Techs (best AI) | Military (best AI) |
|---|---|---|---|---|
| 50 | 105 (1st) | 8 | 13 (15) | 334 (83) |
| 100 | 523 (1st) | 24 | 35 (30) | 1,402 (157) |
| 122 | 715 (1st) | 29 | 47 (34) | 2,447 (252) |

## Final standings (turn 122)

| Civ | Score | Cities | Science / turn | Techs | Military |
|---|---|---|---|---|---|
| **Aztecs (Opus 5.5, winner)** | **715** | **29** | **330** | **47** | **2,447** |
| India | 263 | 6 | 46 | 31 | 252 |
| England | 187 | 2 | 20 | 28 | 91 |
| Greece | 164 | 2 | 63 | 34 | 18 |

Russia, America, Sumeria and China were out by then.

## Three Domination wins

| Game | Civ | Won on turn | Cost | Hours |
|---|---|---|---|---|
| 4 | Sumeria | 169 | $100.64 | 7.6 |
| 24 | Scythia | 149 | $82.02 | 7.1 |
| 28 | Aztecs | 122 | $57.57 | 5.1 |

All three used the same seed and map script. The leader changes the start and the rivals, so the three are not the same game. Game 24 started faster: two capitals by turn 55, against turn 63 here. Game 28 then took the other five in 59 turns, where game 24 took 94.

## The harness in this game

From the run log and the agent's tool results:

- **Rival capitals from the trade route list (found after game 41).** On turn 30 a Trader the game would send nowhere got civ6-mcp's fallback list instead of its destinations: every city of every civ not at war with the Aztecs, 27 in all, among them those of six civs they had not met. Opus wrote the capitals down that turn: "England London (25,29), Sumeria Uruk (39,40), America Washington (50,30), Greece Sparta (57,14), India Delhi (61,34), China Xi'an (70,18). 7 capitals needed. Russia is first target." The Aztecs met them on turns 45 (America) to 70 (Sumeria). So this win knew where the rival capitals stood 15 to 40 turns before it met their civs. The harness gives no such list from game 43 ([setup](../../docs/setup.md)).
- **Peace offers closed as war declarations.** Five times the turn report said "WAR DECLARED by India (Gandhi)! Session dismissed." (turns 105, 114, 117 and 120) or by China (turn 95), each time from a civ already at war with the Aztecs. Opus wrote "India re-declared war (was already at war?)". civ6-mcp treats any session an AI opens during the AI turns as a war declaration when the two civs are at war as it reads it. It closed these sessions unread. Replayed live on the turn-120 save, India's session was a peace offer: a peace treaty both ways, plus 48 gold a turn for 30 turns. Opus had asked India for peace on turns 91 and 105. It was refused both times and never saw India's own offers. Game 24 had 4 more of these (Germany once, Rome 3 times). Fixed from game 29: only a civ at peace when the turn ended counts as declaring, the others' sessions wait for an answer, and deals name the peace treaty, which civ6-mcp had left out.
- **Turns refused over one unit.** On 34 turns, end_turn came back with "the game moved units along their orders, and a unit was left needing orders", and Opus called `skip_remaining_units` again ("double skip", its notes say). The message listed every unit with moves left, already skipped ones included. On turn 120, replayed, it listed 33 units, while the game held the turn for one Field Cannon that had just walked its order. Fixed from game 29: the message names the units the game is waiting on.
- **Other notes Opus left, not looked into yet.** An attack that moved the unit instead (turns 42 and 89), a frigate's move refused as "water tile (can embark)" (turn 107), and a trader refused as `CANNOT_START` with a free route slot (turns 72 and 85).
- No AI-turn hangs, no tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 123 is the agent's closing summary after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100 and 122 (game window on top, war room below).
