# Game 12: game 11 with Fable 5.2 (high effort), goal: Science victory, Online speed

**Result: Science victory on turn 170**, 30 turns earlier than any other game on this setup. Game 12 is game 11 with one change, the model: Fable 5.2 at high effort playing Sumeria (Gilgamesh), against the same 7 built-in AI civs on Prince, on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal, on game 11's harness. Game 10 (Opus 5.5) won on turn 200 and game 9 (Fable 5.1) on turn 203; game 11 (Fable 5.1) lost to Greece's space race on turn 209. The last two space projects finished as turn 170 ended. No AI civ had built a Spaceport.

| | |
|---|---|
| Played | 2026-11-10 11:27 to 17:56 CET, 6.5 hours wall clock, about 38 minutes of it in three AI-turn hangs |
| Turns | 170 (median 104 s per turn) |
| API-equivalent cost | **$91.67** at list prices (Fable 5.2: $8 / $40 per MTok in / out, $0.20 cache read, $16 cache write with the 1-hour TTL). At Fable 5.1's prices the same tokens would cost $114.58 |
| Tokens | 564K output, 205M cache read, 1.76M cache write, 2.1K uncached input |
| API requests | 1,036 (about 6.1 per turn) |
| Tool calls | 1,413, of which 8 returned errors, all `ECONNRESET` (below) |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 5 times |

Cache reads are 45% of the bill ($40.95), cache writes 31% ($28.14) and output 25% ($22.56).

## Final standings (turn 170)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Egypt | 422 | 12 | 89 | 40 | 34 | 232 | 0 |
| **Sumeria (Fable 5.2)** | **417** | 7 | **356** | **64** | **40** | **635** | **3, then 5** |
| Spain | 352 | 8 | 125 | 41 | 33 | 490 | 0 |
| Greece | 350 | 9 | 79 | 46 | 29 | 411 | 0 |
| Brazil | 312 | 6 | 80 | 39 | 28 | 117 | 0 |
| America | 267 | 5 | 43 | 33 | 32 | 372 | 0 |
| Rome | 241 | 6 | 60 | 33 | 27 | 162 | 0 |
| Germany | 239 | 8 | 34 | 30 | 24 | 435 | 0 |

## How it went

Fable 5.2 played tall: 5 cities at turn 100 and 7 at the end, as many as game 9 and fewer than game 11's 11. It traded more than any earlier agent (41 proposals on 8 turns, 16 AI deals answered) and stayed friends or allied with most of the AI civs. Its science per turn was the highest of any civ by turn 98 and reached 332 by turn 150, when its tech lead over the best AI was 13. The first space project came on turn 151, 10 to 24 turns before games 9 to 11. Egypt declared a surprise war on turn 160, with units on the tiles of Lagash, the city with the second spaceport. Machine guns and the city's own attacks held it, Egypt's military fell from 765 to 81 by turn 165, and Egypt asked for peace on turn 170. The Mars Reactor finished at once on turn 169 when the agent used the great person Carl Sagan on it, and the last two Mars projects finished as turn 170 ended.

## Compared with games 9 to 11

| | Game 9 (Fable 5.1, old harness) | Game 10 (Opus 5.5) | Game 11 (Fable 5.1) | Game 12 (Fable 5.2) |
|---|---|---|---|---|
| Result | Science victory, turn 203 | Science victory, turn 200 | Defeat, turn 209 | **Science victory, turn 170** |
| Turn 50: score / cities / techs | 66 / 4 / 9 | 77 / 4 / 14 | 80 / 4 / 12 | 80 / 4 / 13 |
| Turn 100: score / cities / science / techs | 197 / 6 / 71 / 28 | 233 / 8 / 137 / 31 | 196 / 7 / 78 / 31 | 187 / 5 / 98 / 31 |
| Turn 150: score / cities / science / techs | 321 / 7 / 233 / 48 | 346 / 8 / 226 / 48 | 350 / 11 / 180 / 45 | **365** / 7 / **332** / **56** |
| Tech lead over the best AI at turns 100 / 150 | -3 / +8 | +1 / +7 | -4 / -5 | -1 / **+13** (+18 at turn 170) |
| Space projects done (turn reached) | 1 (168), 2 (182), 3 (193), 4 (194), 5 (203) | 1 (161), 2 (179), 3 (184), 4 and 5 (200) | 1 (175), 2 (191), 3 (207), 4 (208) | 1 (151), 2 (161), 3 (169), 4 and 5 (170) |
| Best AI's space projects | 1 | 2 | 5 (Greece won) | 0 |
| Final score and rank | 428, 4th of 8 | 446, 2nd of 8 | 548, 2nd of 8 | 417, 2nd of 8 |
| Cost | $102.47 | $58.24 | $106.37 | $91.67 |
| Cost per turn | $0.505 | $0.291 | $0.509 | $0.539 |
| Requests per turn | 4.5 | 5.5 | 4.0 | 6.1 |
| Output tokens / thinking characters | 468K / 304K | 323K / 215K | 602K / 365K | 564K / 387K |
| Wall clock (median per turn) | 6.0 h of play (84 s) | 5.5 h (62 s) | 6.7 h (94 s) | 6.5 h (104 s) |

Fable 5.2 was not ahead early. At turn 100 it had the lowest score of the four and the fewest cities, and its tech count matched the others. The gap opened between turns 100 and 150, when its science grew to 332 per turn, about 100 more than any other game at that turn. It spent more tokens per turn than Fable 5.1 (6.1 requests per turn against 4.0 to 4.5), and at its lower prices the whole game cost less than either Fable 5.1 game. Games 9 and 11 (the same model and setup: one won on turn 203, the other lost on turn 209) show how far one run can swing, so one game cannot rank Fable 5.2 over the others. [Game 14](../g14-fable52-repeat/) repeated this game and won on turn 168, 1st in score.

## The harness in this game

From the server log and the agent's tool results:

- **Three AI-turn hangs**, on turns 96, 120 and 143, each after trade proposals the AI had accepted that turn. Each time `end_turn` waited about 592 s, civ6-mcp reloaded the turn from its autosave and ended it again (about 13 minutes each), and the turn's orders and trades were undone; `end_turn` said so. Across games 1 to 8, 14 of 23 turns with a trade proposal hung, every one in game 8; with the fix from game 10 on (the diplomacy screen stays up and is closed after the trade), game 11 had 0 of 5 and this game 3 of 8. On every hung turn the last proposals were accepted and no leader screen was closed after them, but game 11 had turns like that too (turns 120 and 192) that did not hang. Replayed live after game 13 from turn 96's autosave, the turn hung again: the agent's trade tests had left Rome holding an empty deal toward the player that the game could never deliver, and Rome's turn waited on it ([setup](../../docs/setup.md) has the details). The trade tools wait for the AI's answer from game 14 on, and the replayed turn then ended in 25 s. Turns 120 and 143 were not replayed.
- **8 tool calls failed with `ECONNRESET`**, one of them an `end_turn`. None reached the server, and the agent sent each one again. All 11 such errors in games 10 to 12 came 4.1 to 5.0 s after the previous result: the client sent on a connection just as uvicorn's 5-second keep-alive timeout closed it. Fable 5.2 more often waits about that long between calls (361 calls 4.5 to 6.5 s after a result, against 166 to 237 in games 10 and 11). Fixed in 46c0e13 (the server keeps idle connections an hour); it loads from game 14.
- **Turn reports kept their events**: the turn snapshot failed 0 times.
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 50 pauses; 33 times the game had already moved to the next turn, and none of those turns ended with no unit order. Fable 5.2 checked the overview after answering an AI civ and played the new turn before calling `end_turn`. The script first missed orders given that way and flagged 3 turns; it now counts the whole new turn (ca9ae0d), which also lowered the counts for games 1, 2, 3 and 6.
- **Moves** said "arrived with no moves left" 81 times, and 3 `improve` orders were refused for lack of moves. **Move-and-attack** results were read again 28 times (3 `STOPPED_SHORT` left). **Auto-explore** was sent again 26 times, `skip_remaining_units` left units with orders of their own alone 97 times, and the harness closed a diplomacy screen left open 30 times.
- `NO_SESSION`, `SILENT_FAILURE` and `InvitePopup` never came up. The spy-mission fix (5379f94) was held back for game 13 so this game ran on game 11's harness; Fable 5.2 sent 8 spy orders and never asked for a missing mission.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 171 is the end of turn 170 (the agent accepted Egypt's peace offer before the victory screen), and row 172 is the agent's closing summary.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 130 and 170 (game window on top, war room below).
