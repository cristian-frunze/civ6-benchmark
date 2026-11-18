# Game 41: Opus 5.5 as England on King, goal: Domination

**Result: Defeat on turn 234. Sumeria (AI) won a Science victory.** Opus 5.5 (high effort) played England (Victoria) on King against seven AI civs: Egypt, Sumeria, America, Brazil, Greece, Russia and India. King is the level between Prince, where Opus won all five of its Domination games, and Emperor, where it lost game 40 as Norway. Map script, size, speed (Online, 250-turn limit) and seed are the same as in the earlier games, and the leader changes the start and the rivals. England finished 2nd of 8 in score (641 to Egypt's 738) with 19 cities, and held three of the seven rival capitals: St. Petersburg (Russia's), Delhi (India's) and Rio de Janeiro (Brazil's). The harness had game 40's fixes.

| | |
|---|---|
| Played | 2026-11-18 09:19 to 18:02 CET, 8.7 hours wall clock, including about 18 minutes on turn 1 (below) |
| Turns | 234 (median 104 s per turn) |
| API-equivalent cost | **$91.41** at list prices, $0.39 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 696K output, 303M cache read, 2.1M cache write, 3.1K uncached input |
| API requests | 1,549 (about 6.6 per turn) |
| Tool calls | 2,178, none returned an error |
| Claude Code sessions | 2. The first drew a Claude account whose login had expired ("this login reached its time limit and cannot be renewed") and ended in 10 seconds with no turn played; the runner marked the account and resumed the same session on another one after 18 minutes of launch pacing on the busy dev box. The second played the whole game and compacted its context six times (turns 75, 118, 158, 191, 215 and 231) |

Cache reads are 66% of the bill ($60.58), cache writes 18% ($16.91) and output 15% ($13.91). Turns 1 to 50 cost $9.22 (median 63 s a turn), 51 to 100 $17.94 (94 s), 101 to 150 $19.28 (103 s), 151 to 200 $21.40 (150 s) and 201 to the end $23.58 (189 s, 10 requests a turn).

## How it went

Opus's turn-1 plan: "England (base game). Goal Domination. Plan: scout, expand to 4-5 cities quickly, then Classical-era rush on nearest neighbor capital with swords/horsemen/catapults." It settled seven cities by turn 77, took Fertility Rites as its pantheon (turn 83) and never founded a religion, and moved from Chiefdom to Oligarchy (turn 46), Monarchy (95) and Merchant Republic (109).

**Russia, three wars for one capital.** The nearest rival was Russia, whose capital, St. Petersburg, stood 20 tiles from London. Opus declared a surprise war on turn 69 with Heavy Chariots, archers, crossbows and rams, and took peace on turn 87 with 7 gold a turn from Russia ("Domination needs a much bigger army plus finding the other 6 civs"). A second war (turns 99 to 113) took nothing. A third, from turn 121 with Bombards, took Voronezh (turn 123) and St. Petersburg (143) with Artillery and Field Cannons, and peace followed on turn 145. Its turn-143 note listed the six capitals left and "107 turns left. Need faster conquest".

**India.** India declared war on turn 154 when Opus refused to pull its army back from the border. Tanks, Artillery and Rocket Artillery took Bangalore (turn 167) and Delhi, India's capital, with its spaceport (turn 189), then Patna (203) and Mumbai (212); India had 3 of the 5 space projects and made no more after Delhi fell. Peace came on turn 213. With two capitals held on turn 189, Opus counted 61 turns left and five capitals to go.

**Brazil, and the debt.** On turn 216 Opus declared war on Brazil and took Brasília (223), Rio de Janeiro (224, Brazil's capital, population 19) and Salvador (227), and made peace on turn 227. Gold income fell from +29 a turn on turn 200 to -81 on turn 224, after the conquests. Then a policy swap in the middle of turn 226 cost about 430 gold, and the treasury went from 252 to -257. The debt cut amenities, rebels rose in several cities, and on turn 228 Opus deleted five Rocket Artillery to cut maintenance; its military went from 1,890 on turn 200 to 931 at the end. Its turn-226 note: "MISTAKE: swapping the Liberalism policy for Triangular Trade mid-turn," and its tooling note, "Policy changes outside civic completion cost gold (not warned by the tool)" (see the harness section).

**The space race.** Opus fought the space race with spies: a Disrupt Rocketry mission on turn 153 and another on turn 220, and five Sabotage Production missions. Sumeria made its first space project on turn 192 and was at 4 of 5 from turn 220. Its last turn's note: "Spy Godgifu is at Bad-Tibira (no space project there) and is travelling to Nina." Sumeria finished at the end of turn 234, 16 turns before the limit. Uruk, Sumeria's capital, stood 18 tiles from London, and England never went to war with Sumeria.

| Turn | Score (rank) | Cities | Science / turn | Techs (most of any AI) | Military (rank) | Gold / turn |
|---|---|---|---|---|---|---|
| 50 | 82 (7th) | 5 | 18 | 14 (Egypt 15) | 191 (2nd) | +16 |
| 100 | 193 (7th) | 7 | 72 | 29 (India 35) | 642 (2nd) | +27 |
| 150 | 327 (5th) | 9 | 175 | 45 (India 56) | 1,322 (1st) | +48 |
| 200 | 435 (4th) | 11 | 140 | 57 (India 66) | 1,890 (1st) | +29 |
| 234 | 641 (2nd) | 19 | 260 | 67 (India 68) | 931 (2nd) | +180 |

England founded 10 cities and took 9.

## Final standings (turn 234)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Egypt | 738 | 14 | 194 | 59 | 51 | 620 | 0 |
| England (Opus 5.5) | 641 | 19 | 260 | 67 | 36 | 931 | 0 |
| America | 581 | 13 | 350 | 67 | 40 | 760 | 1 |
| **Sumeria (winner)** | **581** | **16** | **316** | **68** | **51** | **1,011** | **4, then the last** |
| Brazil | 385 | 6 | 53 | 47 | 51 | 692 | 0 |
| Greece | 366 | 8 | 115 | 62 | 37 | 803 | 3 |
| Russia | 320 | 6 | 162 | 48 | 29 | 229 | 0 |
| India | 301 | 3 | 78 | 68 | 34 | 82 | 3 |

## Against the earlier Domination games and King

| Game | Civ, goal, level | Result | Cost | Hours |
|---|---|---|---|---|
| 24 | Scythia, Domination, Prince | Domination victory, turn 149 | $82.02 | 7.1 |
| 28 | Aztecs, Domination, Prince | Domination victory, turn 122 | $57.57 | 5.1 |
| 34 | Japan, Domination, Prince | Domination victory, turn 236 | $87.65 | 8.4 |
| 37 | Rome, Domination, Prince | Domination victory, turn 176 | $69.47 | 7.8 |
| 40 | Norway, Domination, Emperor | Defeat (Germany, Science), turn 187; tied 4th of 8, 1 rival capital | $66.21 | 5.4 |
| 41 | England, Domination, King | Defeat (Sumeria, Science), turn 234; 2nd of 8, 3 rival capitals | $91.41 | 8.7 |
| 19 | Sumeria, Science, King | Science victory, turn 218; 5th of 8 | $64.28 | 6.4 |

Each civ had its own start and rivals, so the games compare loosely. Here England's first rival capital fell on turn 143, after two wars on the same city ended in peace, and three of seven were not enough by turn 234. Opus's Science win on King (game 19, as Sumeria) came on turn 218, 16 turns before Sumeria's win here.

## The harness in this game

From the run log and the agent's tool results and tooling notes:

- **The game's own combat preview.** 269 of 274 attack estimates came from the game's preview, the fix from game 40: "Bombard" for Rocket Artillery, Bombards and Artillery (75), "Air" for Bombers (8), and 5 from civ6-mcp's own arithmetic. Against the damage the attack then dealt, the median shot fell 2 short of the preview for ranged units and 3.5 for siege units (combat damage in Civ 6 varies at random around it).
- **A refused shot said why, when it could.** Of 16 ranged or siege shots the game refused, two came back "it moved this turn ... siege units fire only before they move" and one "you cannot see that tile now", the fix from game 40; the other 13 had neither cause and said line of sight or an earlier attack.
- **City attacks named the city**, all four war declarations were settled from the game's war state, and 112 orders refused for stacking named the unit of the same formation class.
- **A policy change cost gold without a word (open).** `set_policies` answered `POLICIES_SET|Policies updated` for the swap on turn 226 that cost about 430 gold and put the treasury in debt. The game charges gold to change policies between civics, and the tool neither says the price nor checks it first.
- **Still open:** 21 production orders came back `CANNOT_START` with no reason, 15 of them Traders (four other Trader orders did name the trade route capacity), seven trade routes and one spy trip were refused with no reason, and moves into a civ's land on the turn war was declared on it were blocked (turn 99; game 40 saw the same on turn 88).
- No skipped turns, no AI-turn hangs, no tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 235 is the agent's closing reply after the defeat screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 130, 150, 200 and 234 (game window on top, war room below).
