# Game 9: Fable 5.1 vs the built-in AI, goal: Science victory, Online speed

**Result: Science victory on turn 203**, the earliest of the four games on this setup. It is game 3's setup with one change to the agent: **Fable 5.1** (high effort) instead of Opus 5.5. Everything else is the same as game 3: Sumeria (Gilgamesh), the 7 built-in AI civs on Prince, the same standard Pangaea map and start (same seed), Online speed, the 250-turn limit, the base game, the playbook and the Science goal. It ran on game 8's harness. Game 3 won on turn 212, game 7 (its repeat) on turn 206, and game 8 (Opus at medium effort) on turn 224. Fable finished all five space projects while the best AI civ had one.

| | |
|---|---|
| Played | 2026-11-09 11:07 to 22:51 CET, 6.0 hours of play. Paused from 15:08 to 20:51 at the start of turn 144 so the game PC could be closed (below) |
| Turns | 203 (median 84 s per turn) |
| API-equivalent cost | **$102.47** at list prices (Fable 5.1: $10 / $50 per MTok in / out, $0.25 cache read, $20 cache write with the 1-hour TTL) |
| Tokens | 468K output, 170M cache read, 1.81M cache write, 29K uncached input |
| API requests | 922 (about 4.5 per turn) |
| Tool calls | 1,330, of which 2 returned errors |
| Claude Code sessions | 1, run in two parts around the pause, with no usage limits. Interventions: the pause, the resume, and harness copies to the PC that game 9's server never loaded ([`interventions.jsonl`](interventions.jsonl)) |

Cache reads are 42% of the bill ($42.62), cache writes 35% ($36.18) and output 23% ($23.38).

## Final standings (turn 203)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Egypt | 491 | 12 | 126 | 49 | 51 | 810 | 0 |
| Germany | 434 | 12 | 80 | 39 | 36 | 348 | 0 |
| America | 429 | 10 | 102 | 43 | 39 | 911 | 0 |
| **Sumeria (Fable 5.1)** | **428** | 7 | **224** | **68** | 37 | **995** | **5** |
| Spain | 409 | 9 | 157 | 45 | 46 | 632 | 0 |
| Rome | 386 | 11 | 104 | 50 | 36 | 620 | 1 |
| Brazil | 370 | 9 | 135 | 45 | 26 | 459 | 0 |
| Greece | 295 | 7 | 100 | 44 | 25 | 372 | 1 |

## Compared with games 3, 7 and 8 (same setup, Opus 5.5)

| | Game 3 (high) | Game 7 (high) | Game 8 (medium) | Game 9 (Fable 5.1) |
|---|---|---|---|---|
| Result | Science victory, turn 212 | Science victory, turn 206 | Science victory, turn 224 | Science victory, turn 203 |
| Turn 50: score / cities / techs | 83 / 5 / 11 | 83 / 4 / 12 | 77 / 4 / 11 | 66 / 4 / 9 |
| Turn 100: score / cities / science / techs | 185 / 6 / 66 / 27 | 207 / 8 / 87 / 26 | 212 / 7 / 106 / 33 | 197 / 6 / 71 / 28 |
| Turn 150: score / cities / science / techs | 293 / 6 / 216 / 44 | 339 / 8 / 210 / 47 | 333 / 8 / 259 / 53 | 321 / 7 / 233 / 48 |
| Turn 200: score / science / techs | 387 / 297 / 63 | 418 / 306 / 65 | 421 / 218 / 68 | 423 / 221 / 67 |
| Tech lead over the best AI at turns 100 / 150 / 200 | -4 / +3 / +6 | -7 / +3 / +5 | +2 / +9 / +9 | -3 / +8 / **+18** |
| Space projects done (turn reached) | 2 (183), 3 (201), 4 (205), 5 (212) | 2 (174), 3 (190), 4 (193), 5 (206) | 1 (179), 2 (201), 3 (220), 4 and 5 (224) | 1 (168), 2 (182), 3 (193), 4 (194), 5 (203) |
| Best AI's space projects at the end | 2 | 1 | 4 | 1 |
| Final score and rank | 400, 8th of 8 | 422, 6th of 8 | 453, 4th of 8 | 428, 4th of 8 |
| Cost | $56.43 | $62.87 | $54.83 | $102.47 |
| Cost per turn | $0.265 | $0.304 | $0.245 | $0.505 |
| Requests per turn | 5.2 | 5.7 | 4.9 | 4.5 |
| Output tokens / thinking characters | 331K / 206K | 339K / 212K | 321K / 195K | 468K / 304K |
| Cache reads | 200M | 226M | 198M | 170M |
| Wall clock (median per turn) | 4.6 h (53 s) | 6.6 h (69 s) | 8.6 h, 4.8 h without the hangs (52 s) | 6.0 h of play (84 s) |

Fable started slowest of the four: at turn 50 it had the lowest score (66) and the fewest techs (9). By turn 150 it led the best AI civ by 8 techs, and by turn 200 by 18, twice the largest lead any Opus game reached. Its first space project came on turn 168, 6 to 15 turns before the Opus games' first, and it finished the fifth on turn 203. Rome declared war on turn 194, during the space race. Fable had the strongest military on the map (995, first of 8), and by its own count it killed 8 Roman units for one Machine Gun lost, with no spaceport city ever at risk.

It cost 1.6 to 1.9 times what the Opus games cost. Per token, Fable costs 2.5 times Opus for output and cache writes and 1.25 times for cache reads. It sent fewer requests (922, against 1,112 to 1,172 for Opus at high effort) and read less cache (170M, against 200 to 226M). It wrote about 40% more output and about 45% more thinking than those two games. Its context also filled faster: Claude Code compacted it 4 times, against 3 in every other game, at the same threshold of about 367K tokens. This is one game per model, and games 3 and 7 differed by 6 turns, so a 3-turn win margin over game 7 says little. The tech lead is the clearer difference.

## The pause

The game PC had to be closed in the middle of the game. At the start of turn 144, right after the agent's `end_turn` reported "Turn 143 -> 144", the agent was stopped and the game left running, so the agent had given no orders on turn 144. At 20:51 the PC was back, the game was still on turn 144, and the same Claude Code session was resumed with "Continue", keeping its context. The resume had to rewrite the context cache: turn 144's row holds about 300K tokens of cache writes, about $6 of the bill.

## Harness notes

Game 9 ran on game 8's harness. Fixes made while it ran were copied to the PC but load from game 10 on (see [setup](../../docs/setup.md)).

- **No AI-turn hangs** (game 8: 18, which cost it 3.8 hours).
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 65 diplomacy pauses. 22 times the game had already moved to the next turn before the agent's next `end_turn`, and none of those turns ended with no unit order.
- **A turn that ended was reported as not ended.** The first end turn after the resume closed Brazil's declaration of war and reported "Turn 144 -> 144", although the game was on turn 145. The agent played turn 145 normally. The turn log keys each turn on that header, so turn 145's usage is in turn 144's row, and turn 145's row is empty. The fix is in from game 10.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. The last row (turn 204) is the agent's closing summary after the victory.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`interventions.jsonl`](interventions.jsonl): what was done from outside the agent.
- [`shots/`](shots/): the screens at the start of turns 50, 130 and 200 and at the end (game window on top, war room below).
