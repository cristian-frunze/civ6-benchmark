# Game 21: Opus 5.5 on Emperor again, goal: Science victory, Online speed

**Result: Defeat on turn 169. Greece (AI) won a Science victory.** Game 21 repeats game 20 to see how much one Emperor game says: Opus 5.5 (high effort) as Sumeria (Gilgamesh) against the same 7 built-in AI civs on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. The harness is game 20's plus three fixes: attacks on a city with no unit in it hit the city, a refused trade route says why, and a refused end turn comes back in about 30 s. Opus lost again, earlier and by more: last of 7 in score at the end (Brazil had been eliminated), 22 techs behind Greece, no space project, and two cities lost, Bad-Tibira to Rome on turn 115 and Isin to Egypt on turn 165. What it did differently was spies: two of them set back Greece's rocketry twice, and Greece sat at 3 of 5 space projects from turn 128 to turn 167.

| | |
|---|---|
| Played | 2026-11-12 23:05 to 2026-11-13 02:38 CET, 3.6 hours wall clock, with no stalled end turns |
| Turns | 169 (median 56 s per turn) |
| API-equivalent cost | **$38.83** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 249K output, 137M cache read, 0.81M cache write, 1.5K uncached input |
| API requests | 774 (about 4.6 per turn) |
| Tool calls | 1,202, 12 returned an error (all on turn 82, when the connection to the game PC dropped) |
| Claude Code sessions | 3: the first stopped on turn 82 when the connection dropped, and the runner resumed it twice; no usage limits and no interventions; it compacted its context twice |

Cache reads are 70% of the bill ($27.37), cache writes 17% ($6.48) and output 13% ($4.98). By 50-turn range the game cost $7.21, $16.32, $12.79 and $2.52 (turns 151 to 169, plus the closing summary).

## Final standings (turn 169)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| **Greece (winner)** | **605** | 13 | 294 | **68** | **51** | 1,060 | **4, then 5** |
| Egypt | 556 | 13 | 129 | 46 | **51** | 949 | 0 |
| Germany | 542 | 13 | **306** | 61 | 35 | 1,090 | 1 |
| Rome | 530 | **14** | 184 | 56 | 48 | **1,321** | 3 |
| Spain | 511 | 9 | 290 | 65 | **51** | 575 | 2 |
| America | 393 | 7 | 137 | 61 | 38 | 688 | 2 |
| **Sumeria (Opus 5.5)** | **264** | **6** | **153** | **46** | **22** | **250** | **0** |

Brazil was eliminated: Spain took Salvador da Bahia on turn 43, Germany took Rio de Janeiro on turn 82, and Greece took Brasília, its last city, on turn 149.

## How it went

Opus settled 4 cities by turn 50, with 11 techs to the best AI's 22 and science of 15, the same start as game 20. A barbarian camp to the south held its expansion back for most of the first 60 turns. It had 6 cities at turn 100 (27 techs to the best AI's 45) and founded Lagash, the 7th, on turn 106. Rome, Germany and Egypt denounced it between turns 108 and 111, Egypt "for being weak".

Rome declared war on turn 110 and brought bombards, a legion, a pikeman and a crossbow to Bad-Tibira; Jerusalem joined in. The agent killed a bombard and a crossbow and bought a crossbow for Lagash, but Rome took Bad-Tibira, with its crossbow and builder, on turn 115, the turn the agent founded Eridu; peace came on turn 120. Germany declared war on turn 130, with a military of 1,503 to its 302; German cavalry killed and captured builders, and peace came on turn 140 at the agent's offer. At turn 150 it had 7 cities, 41 techs to the best AI's 62, and science of 162, 5th of 7. Egypt denounced it again on turn 151, declared war on turn 163 and took Isin, which had a crossbow and a warrior inside, on turn 165. The agent planned to offer peace on turn 173 and was building anti-tank crews when the game ended.

Greece finished its first space project on turn 110 and its third by turn 128. The agent saw it on turn 110 ("ALARM") and made spies its plan: it took Diplomatic Service, bought a spy on turn 124 and sent it to Sparta, where it ran Disrupt Rocketry from turn 128. That mission was discovered on turn 132 and the spy was caught escaping. A second spy disrupted Eretria's rocketry on turn 143 and Sparta's on turn 151, then was discovered stealing a tech boost in Eretria and caught escaping on turn 156. Greece stayed at 3 of 5 projects from turn 128 until turn 167, finished its fourth then, and won on turn 169, with the agent's third spy still on its way to Sparta. Opus never finished a Spaceport: Shuruppak's was about 18 turns away. Its score was last at turns 50, 150 and the end, and 7th of 8 at turn 100, ahead of only Brazil; its science ended 5th of 7.

## Emperor: Fable 5.2 twice, Opus 5.5 twice

| | Game 16 (Fable 5.2) | Game 18 (Fable 5.2) | Game 20 (Opus 5.5) | **Game 21 (Opus 5.5)** |
|---|---|---|---|---|
| Result | Defeat, turn 174 (Greece) | Defeat, turn 176 (Greece) | Defeat, turn 186 (America) | **Defeat, turn 169 (Greece)** |
| Turn 50: score / cities / techs (best AI) | 67 / 3 / 12 (21) | 81 / 4 / 12 (25) | 66 / 4 / 11 (22) | **67 / 4 / 11 (22)** |
| Turn 100: score / cities / science / techs (best AI) | 162 / 4 / 51 / 28 (41) | 194 / 7 / 87 / 29 (44) | 182 / 6 / 69 / 28 (45) | **172 / 6 / 67 / 27 (45)** |
| Turn 150: score / cities / science / techs (best AI) | 247 / 6 / 164 / 41 (59) | 283 / 7 / 203 / 45 (63) | 270 / 8 / 108 / 42 (65) | **256 / 7 / 162 / 41 (62)** |
| Tech lead at the end | -16 | -10 | -17 | **-22** |
| Science rank at the end | 2nd | 1st | 6th of 8 | **5th of 7** |
| Its space projects at the end | 0 | 2 | 0 | **0** |
| Wars against it | Spain (turns 82 to 91), Egypt and Rome (121 to 133) | Rome (109 to 119) | Brazil and Spain (29 to 39), Spain (136 to 146), Greece (172 to about 180); its own on Brazil (57 to 67) | **Rome (110 to 120), Germany (130 to 140), Egypt (163 to the end)** |
| Cities lost | Uruk, the capital (turn 86) | none | Kish (turn 146) | **Bad-Tibira (turn 115), Isin (turn 165)** |
| Final score and rank | 283, 8th of 8 | 336, 8th of 8 | 350, 8th of 8 | **264, 7th of 7** |
| Cost (per turn) | $65.14 ($0.374) | $75.31 ($0.428) | $47.67 ($0.255) | **$38.83 ($0.230)** |
| Wall clock (median per turn) | 4.7 h (78 s) | 4.9 h (80 s) | 4.5 h (63 s) | **3.6 h (56 s)** |

The two Opus games started the same way, almost to the number: 4 cities and 11 techs at turn 50 against an AI with 22, and 27 or 28 techs at turn 100 against 45. They split after that on who attacked and who won the space race, not on how Opus played: game 21 drew three wars and lost two cities, and Greece was faster than game 20's America. All four Emperor games ended in a defeat with the agent last in score. Opus is cheaper here than Fable 5.2 ($0.23 and $0.26 a turn, to $0.37 and $0.43) and not better. Two games each is still a small sample, but the line holds for both models: they win up to King and lose from Emperor on.

## The harness in this game

From the server log, the run log and the agent's tool results:

- **The connection to the game PC dropped on turn 82.** The agent runs on the dev server and reaches civ6-mcp on the PC through an SSH tunnel. The tunnel dropped and reconnected 4 times between 00:35 and 00:39 CET; 12 tool calls failed, the first Claude Code session stopped, and the runner resumed it twice (the second session also lost the connection). The agent noted "MCP server disconnected twice at T82; reconnected and orders had applied". The server log shows no fault on the PC. The runner's resume did its job; nothing was lost.
- **No stalled end turns** and no AI-turn hangs. Turn 131 has no row of its own: Germany declared war during turn 130's end turn, and the agent's next steps were counted in turn 130's row (171 s, twice the usual), so there is no screen for turn 131 either. The agent noted "Turn numbering looked odd after the war-declaration interruption".
- **Spy escapes the agent never saw.** When a spy's mission is discovered, the game asks its owner to pick an escape route. civ6-mcp picks one by itself when the agent ends the turn (the City Center on turn 132, the Commercial Hub on turn 156), but it did not say so, and `get_spies` lists nothing while a spy travels, so the agent saw only a prompt it could not answer ("The Choose Escape Route notification isn't handled by the tools") and then no spy. Both spies were caught escaping, which is the game's roll, not the harness.
- **Melee attacks that did not happen.** On hills, forest or across a river, a melee attack with fewer moves left than the target tile costs moved the unit next to the target or did nothing, and the result did not say so clearly (turns 40, 41, 62, 66, 80 and 95). The agent learned to attack only with moves to spare.
- **The screenshots for turns 1 to 145 were skipped at first.** A turn-146 screen left on the PC from a test of game 20's save made the archiver think the game was past turn 145. All of them were copied again after the game, except turn 131's, which was never taken. From game 22, the archiver ignores screens and saves for turns past the game's current turn.
- **Game 20's smaller problems**, fixed after this game and tested on its saves: a city's list of units it can attack now leaves out units of civs at peace (it listed Spanish units in game 21 too); one `send_envoy` call clears the envoy blocker and says how many envoys are left; and the settle advisor lists only tiles nobody else owns.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 170 is the agent's closing summary after the defeat screen; turn 131 is counted in row 130.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 169 (game window on top, war room below).
