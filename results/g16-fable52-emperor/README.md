# Game 16: Fable 5.2 on Emperor, goal: Science victory, Online speed

**Result: Defeat on turn 174. Greece (AI) won a Science victory.** Game 16 puts Fable 5.2 (high effort) on Emperor, the level halfway between Prince, where it won games 12 and 14 (turns 170 and 168), and Deity, where it lost game 15 (turn 132). Everything else is the same: Sumeria (Gilgamesh) against the same 7 built-in AI civs on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. The Emperor start was made with `remote/make-start.sh` and differs from the others only in the difficulty. Fable 5.2 finished last in score; by the end its science was second of 8, but it was still 16 techs behind Greece and America, and its first space project was 9 turns away. The harness is game 15's plus one fix: a trade call empties the deal it leaves behind, so an AI civ's later message no longer shows an old test as its offer (8b5d3f0).

| | |
|---|---|
| Played | 2026-11-11 18:28 to 23:13 CET, 4.7 hours wall clock, with no AI-turn hangs |
| Turns | 174 (median 78 s per turn) |
| API-equivalent cost | **$65.14** at list prices (Fable 5.2: $8 / $40 per MTok in / out, $0.20 cache read, $16 cache write with the 1-hour TTL). At Fable 5.1's prices the same tokens would cost $81.43 |
| Tokens | 370K output, 158M cache read, 1.17M cache write, 1.7K uncached input |
| API requests | 834 (about 4.8 per turn) |
| Tool calls | 1,062, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 3 times |

Cache reads are 49% of the bill ($31.63), cache writes 29% ($18.68) and output 23% ($14.82). By 50-turn range the game cost $10.47, $19.31, $24.05 and $11.32 (turns 151 to 174, plus the closing summary).

## Final standings (turn 174)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| **Greece (winner)** | **576** | 11 | **287** | **66** | 41 | **1,609** | **4, then 5** |
| Germany | 534 | 12 | 68 | 46 | 51 | 568 | 0 |
| Spain | 527 | 10 | 200 | 59 | 51 | 757 | 2 |
| Egypt | 517 | 10 | 106 | 43 | 51 | 773 | 0 |
| Rome | 479 | **14** | 144 | 48 | 45 | 1,195 | 0 |
| Brazil | 400 | 8 | 116 | 46 | 42 | 459 | 0 |
| America | 398 | 9 | 141 | **66** | 36 | 892 | 4 |
| **Sumeria (Fable 5.2)** | **283** | **6** | **248** | **50** | **32** | **562** | 0 |

## How it went

Fable 5.2 was last in score from turn 25 to the end. It had 2 cities at turn 25, 3 at turn 50 and 5 at turn 70; at turn 50 it had 12 techs to the AI's 14 to 21. Spain denounced it on turn 62 and declared war at the end of turn 82 with about three times its military, and took Uruk, the capital, on turn 86. "Science victory now a long shot; priority is survival then rebuilding," the agent wrote on turn 87. Spain refused peace on turn 90, and the war was over by turn 91. With 4 cities at turn 100 (28 techs to the AI's 30 to 41), it founded Shuruppak on turn 118 and had 6 cities again by turn 125. Egypt declared war on turn 121 and Rome on turn 125; a Roman Legion pillaged Kish's Campus, and both wars ended by turn 133 (peace with Egypt by turn 129, with Rome on turn 133) without another city lost. Its science per turn then climbed past most of the AI: 4th of 8 at turn 125, 3rd at turn 150 and 2nd at the end. The tech gap kept growing all the same, from 13 behind the leader at turn 100 to 18 at turn 150 and 16 at the end. America finished the first space project on turn 120 and Greece by turn 122; Greece had 3 by turn 134, 4 on turn 167 and the fifth on turn 174. The agent sent a spy to steal tech boosts from a Greek city (turns 145 and 149), and in the last turns sent spies to sabotage Greece's spaceports: one was killed at Corinth, and the other was still on its mission at Knossos when Greece launched. Its own first Spaceport, in Ur, was finished on turn 174. Its summary after the defeat: "Our science was second of eight (about 243 per turn against Greece's 282), but we were about 18 techs behind and last in score."

## Compared with Prince (games 12 and 14) and Deity (game 15)

| | Game 12 (Prince) | Game 14 (Prince) | **Game 16 (Emperor)** | Game 15 (Deity) |
|---|---|---|---|---|
| Result | Science victory, turn 170 | Science victory, turn 168 | **Defeat, turn 174 (Greece's Science victory)** | Defeat, turn 132 (Greece's Science victory) |
| Turn 50: score / cities / techs | 80 / 4 / 13 | 81 / 5 / 13 | **67 / 3 / 12** | 73 / 3 / 11 |
| Turn 100: score / cities / science / techs | 187 / 5 / 98 / 31 | 239 / 7 / 133 / 31 | **162 / 4 / 51 / 28** | 153 / 4 / 45 / 30 |
| Turn 150: score / cities / science / techs | 365 / 7 / 332 / 56 | 430 / 9 / 298 / 56 | **247 / 6 / 164 / 41** | (game over) |
| Tech lead over the best AI at turns 100 / 150 | -1 / +13 | +3 / +15 | **-13 / -18** | -19 / (game over) |
| Best AI's space projects | 0 | 0 | **5 (Greece), 4 (America)** | 5 (Greece) |
| Cities lost | none | none | **Uruk (turn 86, to Spain)** | Eridu, Uruk, Sippar (turns 91 to 108) |
| Final score and rank | 417, 2nd of 8 | 471, 1st of 8 | **283, 8th of 8** | 191, 8th of 8 |
| Cost (per turn) | $91.67 ($0.539) | $79.27 ($0.472) | **$65.14 ($0.374)** | $51.00 ($0.386) |
| Wall clock (median per turn) | 6.5 h (104 s) | 5.7 h (105 s) | **4.7 h (78 s)** | 3.5 h (68 s) |

On Emperor, Fable 5.2's lead from Prince was gone. Its game looked like the Deity game, only slower: a small, slow start (3 cities and 12 techs at turn 50, against 4 or 5 cities and 13 techs on Prince), an AI invasion in the 80s that took the capital, and a tech gap that grew to 18 by turn 150, where on Prince it led by 13 and 15. Each AI civ starts with 4 units on Emperor (2 on Prince, 6 on Deity) and gets yield bonuses, and Greece won on turn 174, only 4 to 6 turns later than Fable 5.2's own Prince wins. Fable 5.2 raised its science to second of 8 in the last 25 turns, too late. One game per level is a small sample, but the step from a win on Prince to a loss came by Emperor, not only at Deity.

## The harness in this game

From the server log and the agent's tool results:

- **No AI-turn hangs and no tool errors.**
- **One end turn refused over a unit, reported in 71 s.** On turn 123 the game held the end turn because a unit needed orders. From game 15, `end_turn` checks at 45 s and names the unit; in games 2 to 14, each of these waits took about 10 minutes. This was its first use in a game.
- **No old trades shown as offers.** The agent accepted 5 AI offers (an Open Borders swap with Spain, Horses for Incense with America, an alliance with America, and two deals with Germany), and every one went into effect; none repeated terms it had tested before. In game 15, 7 of 8 had.
- **Trade tests**: 30 on turns 70, 80, 83, 84, 86 and 129: 5 `ACCEPTABLE`, 17 `NOT ACCEPTABLE as-is`, 6 `REJECTED` and 2 with no answer (both Brazil). It then sent 5 proposals: Open Borders to Brazil, Horses to America for 148 gold and Citrus to Germany for 163 gold were accepted, and Horses to Brazil was refused twice.
- **Leader screens**: the harness closed a leader screen left open after a diplomacy answer 52 times, and left one alone 30 times because a diplomacy session was still open.
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 46 pauses; 25 times the game had already moved to the next turn, and 2 of those turns ended with no unit order.
- **Moves** said "arrived with no moves left" 80 times, and no move-and-attack stopped short. **Auto-explore** was sent again 30 times, and `skip_remaining_units` left units with orders of their own alone in all 127 of its calls.
- **Spies**: 2 `STEAL_TECH_BOOST` missions against Greece and 2 `DISRUPT_ROCKETRY` missions against its spaceports went out; one more was refused because the spy had not reached the city yet.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 175 is the agent's summary after the defeat screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 174 (game window on top, war room below).
