# Game 18: game 16 again (Fable 5.2 on Emperor), goal: Science victory, Online speed

**Result: Defeat on turn 176. Greece (AI) won a Science victory.** Game 18 repeats game 16 exactly: Fable 5.2 (high effort) playing Sumeria (Gilgamesh) on Emperor, against the same 7 built-in AI civs on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. Fable 5.2 won on Prince (games 12 and 14) and King (game 17) and lost game 16 on Emperor, where Spain took its capital on turn 86, so the question was whether the Emperor loss repeats without that blow. It did: no city fell this time, and by the end Fable 5.2 had the highest science of any civ, but it was 10 techs behind Greece, finished last in score, and had 2 of the 5 space projects when Greece launched its fifth. The harness is games 16 and 17's, unchanged.

| | |
|---|---|
| Played | 2026-11-12 04:57 to 09:52 CET, 4.9 hours wall clock, with no AI-turn hangs |
| Turns | 176 (median 80 s per turn) |
| API-equivalent cost | **$75.31** at list prices (Fable 5.2: $8 / $40 per MTok in / out, $0.20 cache read, $16 cache write with the 1-hour TTL). At Fable 5.1's prices the same tokens would cost $94.14 |
| Tokens | 444K output, 185M cache read, 1.29M cache write, 1.9K uncached input |
| API requests | 953 (about 5.4 per turn) |
| Tool calls | 1,186, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 3 times |

Cache reads are 49% of the bill ($36.98), cache writes 27% ($20.57) and output 24% ($17.75). By 50-turn range the game cost $9.87, $23.23, $27.65 and $14.56 (turns 151 to 176, plus the closing summary).

## Final standings (turn 176)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Egypt | **547** | 12 | 136 | 49 | **51** | 1,040 | 0 |
| Rome | 543 | **13** | 147 | 53 | **51** | **1,673** | 0 |
| **Greece (winner)** | 530 | 12 | 218 | **68** | 44 | 1,522 | **4, then 5** |
| Germany | 530 | 10 | 240 | 63 | 37 | 754 | 0 |
| Spain | 489 | 9 | 252 | 63 | **51** | 436 | 3 |
| America | 444 | 10 | 216 | 61 | 36 | 205 | 3 |
| Brazil | 354 | 8 | 106 | 45 | 39 | 690 | 0 |
| **Sumeria (Fable 5.2)** | **336** | **7** | **292** | **58** | **34** | **650** | **2** |

## How it went

The start was again slow, though less than in game 16: 4 cities at turn 50 (game 16: 3), but still 12 techs to the AI's 16 to 25. It had 7 cities by turn 97 and kept all of them. It lost a Builder and a Scout to attacks, and Rome captured another Builder. Rome, Spain and Egypt denounced it; Rome declared war on turn 109, when Fable 5.2 was allied with Germany, which was already at war with Rome, and made peace on turn 119 without taking a city. Science climbed from 8th of 8 at turn 50 to 5th at turn 100, 2nd at turn 150 and 1st at the end (292 per turn), with a Research Lab in all 7 cities. The tech gap to the leader, Greece, still grew from 15 at turn 100 to 18 at turn 150, then shrank to 10 at the end. Greece finished its first space project by turn 117 and had 3 by turn 146. From turn 125 the agent sent spies to Olympia to set back Greece's rocketry; one mission succeeded (turn 161), and two spies were captured and one killed. Its own first Spaceport came on turn 153: the Earth Satellite was done as turn 160 ended and the Moon Landing as turn 174 ended, when Spain and America had 3 each. Greece finished its fourth project as turn 175 ended and its fifth as turn 176 ended. The agent's summary: "Greece had been at 3/5 since T146 with three spaceports, while my first spaceport was only finished on T153 and the second on T168."

## Game 16 and game 18, both on Emperor

| | Game 16 | **Game 18** | Game 17 (King, for reference) |
|---|---|---|---|
| Result | Defeat, turn 174 (Greece) | **Defeat, turn 176 (Greece)** | Science victory, turn 170 |
| Turn 50: score / cities / techs (best AI) | 67 / 3 / 12 (21) | **81 / 4 / 12 (25)** | 74 / 4 / 13 (15) |
| Turn 100: score / cities / science / techs (best AI) | 162 / 4 / 51 / 28 (41) | **194 / 7 / 87 / 29 (44)** | 238 / 8 / 101 / 31 (35) |
| Turn 150: score / cities / science / techs (best AI) | 247 / 6 / 164 / 41 (59) | **283 / 7 / 203 / 45 (63)** | 396 / 8 / 317 / 57 (48) |
| Tech lead at the end | -16 | **-10** | +14 |
| Science rank at the end | 2nd | **1st** | 1st |
| Its space projects at the end | 0 | **2** | 5 |
| Wars against it | Spain (turns 82 to 91), Egypt and Rome (121 to 133) | **Rome (109 to 119)** | none |
| Cities lost | Uruk, the capital (turn 86) | **none** | none |
| Final score and rank | 283, 8th of 8 | **336, 8th of 8** | 442, 1st of 8 |
| Cost (per turn) | $65.14 ($0.374) | **$75.31 ($0.428)** | $71.03 ($0.418) |

The Emperor loss repeated without the lost capital. Both Emperor games went the same way: by turn 50 the leading AI civ had nearly twice Fable 5.2's techs (21 and 25 to its 12; on King, 15 to its 13). Fable 5.2 then out-researched every AI civ by the end, but it never caught up with Greece's head start, and Greece finished its space race on turns 174 and 176. On King it led in science from turn 71 and in techs from turn 125. With games 12, 14 and 17, Fable 5.2 has won all 3 games up to King and lost all 3 from Emperor up (games 15, 16 and 18).

## The harness in this game

From the server log and the agent's tool results:

- **No AI-turn hangs, no tool errors, and no end turns refused over a unit.**
- **Screenshots for turns 1 to 169 were not synced during the game, and were recovered after it.** Game 18 started 7 minutes after game 17 ended. The capture loop on the game PC follows the game named in its request file, but it reads the turn from civ6-mcp's heartbeat, which at that moment still held game 17's last turn, 170. It saved a `T0170.jpg` into game 18's folder at once, and `tools/archive.py`, which syncs only shot names that sort after the newest one it holds, skipped every turn below 170. All 176 shots were still on the PC, and a resync with the watermark cleared brought them over. From game 19 the loop saves a turn only when the heartbeat's `run_id` names the requested game.
- **Trades**: the agent tested two trades (turn 40, no answer; turn 146, not acceptable) and proposed none. It answered 11 AI offers: 7 accepted and 4 refused.
- **Leader screens**: the harness closed a leader screen left open after a diplomacy answer 9 times, and left one alone 42 times because a diplomacy session was still open.
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 50 pauses; 42 times the game had already moved to the next turn, and 5 of those turns ended with no unit order.
- **Moves** said "arrived with no moves left" 95 times. **Move-and-attack** left 3 `STOPPED_SHORT`. **Auto-explore** was sent again 16 times, and `skip_remaining_units` left units with orders of their own alone in all 117 of its calls.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 177 is the agent's summary after the defeat screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150, 170 and 176 (game window on top, war room below).
