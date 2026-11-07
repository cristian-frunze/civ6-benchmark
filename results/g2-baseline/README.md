# Game 2: Opus 5.5 vs the built-in AI, rules only

**Result: Science victory on turn 266.** Same setup as [game 1](../g1-standard/): Opus 5.5 (high effort) as Sumeria (Gilgamesh) against 7 built-in AI civs on Prince, standard Pangaea, Quick speed, base game, same seed and start save. The only change is the system prompt: CivBench's minimal baseline (the rules and the tools) instead of the civ6-mcp strategy playbook. It won 4 turns later than game 1, by the same route.

| | |
|---|---|
| Played | 2026-11-06 to 07, 7.1 hours wall clock |
| Turns | 266 (median 53 s per turn) |
| API-equivalent cost | **$72.32** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL). About $7 of it went to two harness stalls (below) |
| Tokens | 390K output, 268M cache read, 1.35M cache write, 2.9K uncached input |
| API requests | 1,461 (about 5.5 per turn) |
| Tool calls | 2,006, of which 10 returned errors |
| Claude Code sessions | 15, all one conversation (14 resumes during the turn 238 stall, no usage limits hit) |

Cache reads are most of the bill again ($53.69). Output was $7.80 and cache writes $10.83.

## Final standings (turn 266)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| Greece | 572 | 13 | 236 | 58 | 51 | 871 |
| Egypt | 516 | 14 | 121 | 49 | 51 | 459 |
| Brazil | 437 | 7 | 114 | 42 | 51 | 268 |
| **Sumeria (Opus 5.5)** | 435 | 8 | 188 | **68** | 33 | 762 |
| Spain | 398 | 8 | 210 | 55 | 43 | 616 |
| Rome | 386 | 10 | 154 | 59 | 34 | 315 |
| Germany | 242 | 6 | 40 | 32 | 29 | 645 |
| America | 223 | 4 | 59 | 37 | 26 | 316 |

Opus finished fourth on score with fewer cities and civics than game 1, but it had every tech by turn 237 and built the five space projects first. Its science per turn at the end is below Greece's because it had moved its policies from science to production for the projects.

## Compared with game 1

| | Game 1 (playbook) | Game 2 (rules only) |
|---|---|---|
| Result | Science victory, turn 262 | Science victory, turn 266 |
| Cost | $67.83 | $72.32 (about $65 without the two stalls) |
| Median seconds per turn | 47 | 53 |
| Requests per turn | 5.0 | 5.5 |
| Tech lead over the best AI | -4 to +10, +7 at the end | -5 to +13, +9 at the end |
| Lead stays above zero from | turn 147 | turn 172 |
| Median length of the five reflections per turn | 283 characters | 140 characters |

Without the playbook Opus fell further behind on techs in the middle game (5 behind the best AI as late as turn 139) and took the lead for good on turn 172, 25 turns later than game 1, then pulled ahead faster. Its diary got terser: on 94 turns at least two of the five reflections began with "Same" (42 in game 1). `tools/report.py` draws both games' cost and tech lead turn by turn.

## Cost and pace over the game

| Turns | API-equivalent $ | Median seconds per turn | Requests per turn |
|---|---|---|---|
| 1-50 | 6.59 | 38 | 5.0 |
| 51-100 | 15.99 | 59 | 5.9 |
| 101-150 | 18.45 | 109 | 7.2 |
| 151-200 | 13.26 | 46 | 4.1 |
| 201-250 | 14.98 | 57 | 6.2 |
| 251-266 | 3.04 | 35 | 2.4 |

The 101-150 range includes the turn 144-145 stall, and 201-250 includes turn 238 ($5.82 on its own).

## Harness incidents and interventions

- **Turns 144-145: two hangs and a screensaver.** An AI trade proposal paused the end of turn 144, and the turn number then read 145 before Opus's turn had started. Its moves failed and the next `end_turn` hung. civ6-mcp reports a hang after about 9 minutes and tells the agent to reload the turn's save, which relaunches the game and clicks through the menus. The clicks failed because the Asus "OLED Care" screensaver had taken over the screen. We stopped it and turned the screensaver off; the reload then worked. The `end_turn` checks were changed afterwards so they wait for the player's turn first (deployed on turn 238).
- **Turn 238: Future Tech.** Opus had every tech, so the game asked for Future Tech again, which repeats. civ6-mcp's `set_research` refused anything already researched, so `end_turn` reported a research blocker every time. Opus worked out the cause. To get unstuck it also reloaded the turn's autosave, which relaunched the game into the screensaver: Asus software had switched it back on. Its session ended at 03:14 with a clear report that the tool needed a fix; the runner then resumed it 13 times in 7 minutes, and each resume retried for about 25 seconds and said the same. We stopped the screensaver for good with a keep-awake task, and deployed a fix that lets `set_research` pick a repeatable tech again. The turn then ended normally.

Everything done to the game from outside the agent is in [interventions.jsonl](interventions.jsonl). None of it changed the game state. Both reloads went back to the start of the same turn.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and every city.
- [`shots/`](shots/): the screens at the start of turns 50, 130, 200 and the end (game window on top, war room below).
- [`interventions.jsonl`](interventions.jsonl): every action on the running game from outside the agent.
