# Game 31: Opus 5.5 as Russia on Prince, goal: Religious victory, fixed harness

**Result: Defeat. Greece (AI) won a Science victory on turn 223, with Russia 6th of 8 in score.** Opus 5.5 (high effort) replayed game 29's start: Russia (Peter the Great) against Egypt, Greece, Germany, Rome, Brazil, America and Sumeria, on the same map, seed, speed (Online, 250-turn limit) and difficulty (Prince). The harness had game 29's fixes: a religion count per civ, theological combat in the attack tool's description, a war-type check with the game's reason, Evangelize Belief, Launch Inquisition and Remove Heresy orders, and a wonder advisor that lists only tiles the game accepts.

Eastern Orthodoxy was the majority religion in 4 of 8 civs at the end (Russia, Rome, Brazil and America), 5 of 8 at its best (turns 190 to 210). Game 29 reached 6 of 8 and lost to Egypt's culture; game 31 lost to Greece's space race.

| | |
|---|---|
| Played | 2026-11-15 09:26 to 16:19 CET, 6.9 hours wall clock |
| Turns | 223 (median 98 s per turn) |
| API-equivalent cost | **$84.74** at list prices, $0.38 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 589K output, 284M cache read, 2.01M cache write, 2.9K uncached input |
| API requests | 1,471 (about 6.6 per turn) |
| Tool calls | 2,054, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions. It compacted its context 5 times (turns 98, 136, 158, 180 and 204) |

Cache reads are 67% of the bill ($56.83), cache writes 19% ($16.11) and output 14% ($11.78). Turns 1 to 50 cost $6.14 (median 49 s a turn), 51 to 100 $15.67 (63 s), 101 to 150 $23.09 (109 s), 151 to 200 $29.32 (144 s), and 201 to the end $10.52 (136 s).

## How it went

Same start, another game. Opus founded Eastern Orthodoxy earlier than in game 29 (turn 23, with Work Ethic and Pilgrimage), but barbarians held the start back: 2 cities at turn 50 (game 29: 3) and 6 at turn 100 (game 29: 10). Russia was 6th of 8 in score at turn 100, where game 29 led.

Faith went into Apostles again: 54 bought, and 2 Missionaries. From turn 102 the Apostles fought: 17 theological attacks on Egyptian and Sumerian religious units, 6 of them kills. Sumeria's Inquisitors still turned converted cities back to Sikhism: Ur and Bad-Tibira by turn 192, then Uruk, Shuruppak and Ur on turn 215. The religion count gave Opus each civ's gap every 10 turns, for example at turn 200: "Egypt is 4 of 10 (need 2 more), Sumeria 2 of 12 (need 5 more), Germany 0 of 10 (need 6)". Germany never came close: 1 of 11 cities at the end.

Greece won the space race. Opus saw it early: "THREAT: Greece's science victory is perhaps 10-15 turns away (3/5)" on turn 175, and it fought Greece three times:

| Turns | Event |
|---|---|
| 158-168 | Formal war on Greece, for religious access. Opus then found its Apostles blocked from Greek territory, and made peace on turn 168 with open borders |
| 168-178 | Egypt declared war on Russia; peace on turn 178. Russia went bankrupt around turn 171 and units were disbanded |
| 172 | A spy's Disrupt Rocketry at Sparta |
| 185-194 | Surprise war on Greece. Cossacks pillaged an Aerodrome, a mine, a research lab and a university near Ephesus, but the game refused to pillage the Spaceport with no reason (turns 186 and 187), and Opus concluded Spaceports cannot be pillaged |
| 219 | Greece's 4th project (its 3rd had been on turn 175) |
| 223 | Another Disrupt Rocketry at Sparta and a third war; Greece finished the 5th project that turn |

Opus's closing summary: "I let Greece's space programme go unwatched for too long", and "I should have stopped Greece's space projects (with a spy or an early attack on the spaceports) as soon as Greece reached 3 of 5 around turn 194, instead of putting every resource into missionaries and apostles." Greece had 3 projects from turn 175.

| Turn | Score (rank) | Cities | Techs (best AI) | Faith / turn | Military (best AI) |
|---|---|---|---|---|---|
| 50 | 67 (6th) | 2 | 11 (14) | 5 | 134 (136) |
| 100 | 177 (6th) | 6 | 19 (33) | 51 | 151 (617) |
| 150 | 310 (4th) | 9 | 35 (45) | 195 | 333 (791) |
| 200 | 382 (5th) | 9 | 46 (64) | 282 | 802 (828) |
| 223 | 397 (6th) | 9 | 49 (68) | 294 | 770 (957) |

## Final standings (turn 223)

| Civ | Score | Cities | Science / turn | Techs | Military | Faith / turn | Space projects |
|---|---|---|---|---|---|---|---|
| Rome | 503 | 10 | 90 | 49 | 814 | 43 | 0 |
| Egypt | 503 | 11 | 119 | 47 | 847 | 160 | 0 |
| **Greece (winner)** | **492** | **10** | **278** | **68** | **141** | **4** | **4, the 5th on turn 223** |
| Germany | 486 | 11 | 83 | 43 | 927 | 82 | 0 |
| America | 422 | 9 | 152 | 56 | 604 | 18 | 2 |
| Russia (Opus 5.5) | 397 | 9 | 97 | 49 | 770 | 294 | 0 |
| Sumeria | 397 | 12 | 141 | 56 | 465 | 97 | 0 |
| Brazil | 362 | 6 | 61 | 40 | 957 | 15 | 0 |

## Two Russia games

| Game | Harness | Result | Orthodox majority at the end | Cities at turn 100 | Apostles bought | Cost | Hours |
|---|---|---|---|---|---|---|---|
| 29 | game 28's | Defeat (Egypt, Culture), turn 224 | 6 of 8 | 10 | 56 | $90.88 | 9.0 |
| 31 | game 29's fixes | Defeat (Greece, Science), turn 223 | 4 of 8 | 6 | 54 | $84.74 | 6.9 |

Same start, same rivals, and each game lost to a different AI victory. The fixed harness gave Opus the per-civ religion count and theological combat, which it used, but game 31 started weaker (barbarians) and spent turns 158 to 194 in wars. One pair of games can't separate the harness from the start.

## The harness in this game

From the run log and the agent's tool results:

- **The religion count and theological combat were used.** Every 10-turn snapshot named each civ's gap, and Opus's plans followed it. Apostles attacked 17 times, killing 6 religious units.
- **The Evangelize Belief order was never used.** On turn 85 Opus bought an Apostle to add a belief and wrote "'evangelize' isn't among the unit_action options and I'm not sure how to trigger it". The order was described at the end of `unit_action`'s description, but the tool's list of actions ("action: One of: move, attack, ...") did not name it, nor `launch_inquisition` or `remove_heresy`. Orthodoxy kept its two founding beliefs, as in game 29. Fixed from game 33: the list names them.
- **"BLOCKED (foreign territory) - need Open Borders" after Opus had bought open borders.** 58 moves came back with this reason, many into Greece, Germany and Egypt (turn 210: "Multi-tile moves report BLOCKED even in Greek territory where I have open borders; 1-tile hops work"). Replaying this game's saves afterwards found two faults. civ6-mcp added open borders to a deal with no duration, so the game took Russia's gold and the borders lasted 0 turns: on turn 210 Opus did not have them. And civ6-mcp guesses the reason from who owns the target tile, while religious units need no open borders: the Apostle checked on turn 216 had moved into a unit's zone of control. Fixed from game 33: an agreement in a deal gets the duration the game offers, and a blocked move names the game's facts (zone of control, open borders for land combat units only, the game's own path).
- **A Spaceport the game would not pillage, with no reason** (turns 186 and 187), as in game 26. The game's data gives Spaceports a pillage yield (25 science), so the refusal has another cause. To be looked into on this game's save.
- **A war declaration that took a second try** (turn 223): "DECLARE_SURPRISE_WAR did not take effect. Send it again", and the second call worked.
- The war-type check had nothing to refuse (all three declarations were types the game accepted). The wonder advisor was called only twice. No AI-turn hangs, no tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 224 is the agent's closing summary after the defeat screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150, 200 and 223 (game window on top, war room below).
