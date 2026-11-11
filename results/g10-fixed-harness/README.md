# Game 10: game 3 repeated on the fixed harness (Opus 5.5, high effort), goal: Science victory, Online speed

**Result: Science victory on turn 200**, the earliest of the five games on this setup. Game 10 is game 3 run again with the same agent and prompt: Opus 5.5 at high effort playing Sumeria (Gilgamesh), against the same 7 built-in AI civs on Prince, on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. The one change is the harness: every fix through commit 57e7e5c (see [setup](../../docs/setup.md)). It is the baseline for games 8 and 9 and a measure of the fixes. Game 3 won on turn 212 and game 7 (game 3 repeated on the old harness) on turn 206. The fifth space project finished as turn 200 ended. The agent counts that as turn 201; the other games count the last turn played, as here.

| | |
|---|---|
| Played | 2026-11-09 22:57 to 2026-11-10 04:26 CET, 5.5 hours wall clock, about 1 hour of it in 6 end turns the game refused over a unit (see below) |
| Turns | 200 (median 62 s per turn) |
| API-equivalent cost | **$58.24** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 323K output, 206M cache read, 1.33M cache write, 2.2K uncached input |
| API requests | 1,103 (about 5.5 per turn) |
| Tool calls | 1,543, of which 2 returned errors |
| Claude Code sessions | 1, with no usage limits and no interventions |

Cache reads are 71% of the bill ($41.15). Output was $6.47 and cache writes $10.61.

## Final standings (turn 200)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Egypt | 490 | 10 | 177 | 56 | 45 | 918 | 0 |
| **Sumeria (Opus 5.5)** | **446** | 8 | **331** | **67** | 38 | 789 | **4, then 5** |
| Brazil | 425 | 9 | 84 | 45 | 39 | 200 | 0 |
| Greece | 400 | 10 | 195 | 61 | 34 | 195 | 2 |
| Spain | 387 | 8 | 157 | 49 | 35 | 1057 | 1 |
| Rome | 382 | 10 | 124 | 45 | 35 | 573 | 0 |
| America | 346 | 7 | 82 | 42 | 33 | 438 | 0 |
| Germany | 308 | 7 | 59 | 37 | 31 | 47 | 0 |

## Compared with games 3 and 7 (same setup, old harness) and games 8 and 9

| | Game 3 | Game 7 | Game 10 (fixed harness) | Game 8 (Opus medium) | Game 9 (Fable 5.1) |
|---|---|---|---|---|---|
| Result | Science victory, turn 212 | Science victory, turn 206 | **Science victory, turn 200** | Science victory, turn 224 | Science victory, turn 203 |
| Turn 50: score / cities / techs | 83 / 5 / 11 | 83 / 4 / 12 | 77 / 4 / 14 | 77 / 4 / 11 | 66 / 4 / 9 |
| Turn 100: score / cities / science / techs | 185 / 6 / 66 / 27 | 207 / 8 / 87 / 26 | 233 / 8 / 137 / 31 | 212 / 7 / 106 / 33 | 197 / 6 / 71 / 28 |
| Turn 150: score / cities / science / techs | 293 / 6 / 216 / 44 | 339 / 8 / 210 / 47 | 346 / 8 / 226 / 48 | 333 / 8 / 259 / 53 | 321 / 7 / 233 / 48 |
| Turn 200: score / science / techs | 387 / 297 / 63 | 418 / 306 / 65 | 446 / 331 / 67 | 421 / 218 / 68 | 423 / 221 / 67 |
| Tech lead over the best AI at turns 100 / 150 / 200 | -4 / +3 / +6 | -7 / +3 / +5 | +1 / +7 / +6 | +2 / +9 / +9 | -3 / +8 / +18 |
| Space projects done (turn reached) | 2 (183), 3 (201), 4 (205), 5 (212) | 2 (174), 3 (190), 4 (193), 5 (206) | 1 (161), 2 (179), 3 (184), 4 and 5 (200) | 1 (179), 2 (201), 3 (220), 4 and 5 (224) | 1 (168), 2 (182), 3 (193), 4 (194), 5 (203) |
| Final score and rank | 400, 8th of 8 | 422, 6th of 8 | **446, 2nd of 8** | 453, 4th of 8 | 428, 4th of 8 |
| Cost | $56.43 | $62.87 | $58.24 | $54.83 | $102.47 |
| Cost per turn | $0.265 | $0.304 | $0.291 | $0.245 | $0.505 |
| Requests per turn | 5.2 | 5.7 | 5.5 | 4.9 | 4.5 |
| Output tokens / thinking characters | 331K / 206K | 339K / 212K | 323K / 215K | 321K / 195K | 468K / 304K |
| Wall clock (median per turn) | 4.6 h (53 s) | 6.6 h (69 s) | 5.5 h (62 s) | 8.6 h, 4.8 h without the hangs (52 s) | 6.0 h of play (84 s) |

On the fixed harness, the same agent won 12 turns earlier than game 3 and 6 earlier than game 7, for about the same cost and the same amount of thinking. It was ahead from turn 100 on: its score was the highest of the three at turns 100, 150 and 200, and at turn 100 it made twice game 3's science (137 to 66). It also finished higher, 2nd of 8 against 8th and 6th. Its first space project came 13 to 22 turns earlier than in games 3 and 7. Games 3 and 7 differed by 6 turns with identical setups, so one game cannot separate the fixes from the spread between games. What the fixes did change is the friction, below. By its own account, the agent stayed out of every war through alliances and friendships, Spain's military was about 1.5 times its own, and its one idle spaceport and a rejected Great Engineer were its main mistakes.

## The fixes at work

From the server log and the agent's tool results:

- **No AI-turn hangs** (game 8: 18, which cost it 3.8 hours). The agent proposed no trades, which caused most of game 8's hangs. It did answer 45 AI deals and took 118 other diplomatic actions, and 27 times the harness closed a diplomacy screen those had left open.
- **Six end turns refused over a unit, 59 minutes in all** (turns 35, 103, 106, 123, 157 and 162; found after game 13). When the turn ends, the game first moves units along their multi-turn orders. A unit can come out of that with moves left and no orders, and the game then refuses the turn end. civ6-mcp waited its full 10 minutes for a turn change and named the blocker ("End turn blocked: Units"), and one more skip ended the turn. From game 10 `skip_remaining_units` leaves units on multi-turn moves alone, which made this more common (games 1 to 9: at most 2 a game). The harness names the blocker at 45 s from game 15 on ([setup](../../docs/setup.md)).
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 55 pauses. The game had already moved to the next turn 12 times, and each time `end_turn` reported the new turn. None of those turns ended with no unit order.
- **Auto-explore** was sent again 67 times, so scouts kept exploring from turn to turn.
- **`skip_remaining_units`** left units with orders of their own alone in 167 calls.
- **Move-and-attack** results were read again after the order played out 24 times, instead of civ6-mcp's false "STOPPED_SHORT". The 4 `STOPPED_SHORT` left were one real case, sent several times.
- **Moves** said "arrived with no moves left" 73 times. 1 `improve` order was refused for lack of moves, against 4 to 34 in each earlier Science game (games 1 to 3 and 5 to 9, same count).
- **The promotion blocker** named the units every time (games 1 to 9: 12 to 118 unnamed blockers a game).
- **Diplomacy pauses** carried player ids. The one `NO_SESSION` said that no session was open. `SILENT_FAILURE` never came up (games 1 to 9: up to 5 a game), and `InvitePopup` was gone from the popup scan.

Still unfixed in this game: 42 of the 200 turn reports lost their events because the turn snapshot failed. The cause was found during the game (setup: "One turn report in six lost its events"). The fix loads from game 11.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. The last row (turn 201) is the agent's closing summary after the victory.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 130 and 200 (game window on top, war room below).
