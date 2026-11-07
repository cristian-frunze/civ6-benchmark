# Game 3: Opus 5.5 vs the built-in AI, goal: Science victory, Online speed

**Result: Science victory on turn 213.** Opus 5.5 (high effort) played Sumeria (Gilgamesh) against the same 7 built-in AI civs on Prince, on the same standard Pangaea map and start as games 1 and 2 (same seed), base game, with the playbook. Two things changed: the game speed is Online (250-turn limit instead of Quick's 330), and the system prompt names a goal, a Science victory, while every victory type stays on for every civ. It won by its goal, 37 turns before the limit.

| | |
|---|---|
| Played | 2026-11-07, 4.6 hours wall clock |
| Turns | 213 (median 53 s per turn) |
| API-equivalent cost | **$56.43** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 331K output, 200M cache read, 1.21M cache write, 2.2K uncached input |
| API requests | 1,112 (about 5.2 per turn) |
| Tool calls | 1,609, of which 2 returned errors |
| Claude Code sessions | 1: the whole game in one conversation, with no restarts, usage limits or interventions |

Cache reads are most of the bill again ($40.09). Output was $6.61 and cache writes $9.72.

## Final standings (turn 212)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Egypt | 490 | 12 | 121 | 50 | 51 | 565 | 0 |
| Rome | 455 | 11 | 278 | 63 | 40 | 652 | 1 |
| Greece | 443 | 11 | 169 | 54 | 37 | 91 | 2 |
| Germany | 430 | 10 | 161 | 51 | 35 | 283 | 0 |
| Spain | 422 | 8 | 215 | 60 | 51 | 411 | 2 |
| Brazil | 411 | 7 | 70 | 41 | 47 | 351 | 0 |
| America | 405 | 8 | 103 | 47 | 36 | 793 | 0 |
| **Sumeria (Opus 5.5)** | 400 | 6 | **303** | **67** | 36 | 505 | 4, then the 5th on turn 213 |

This was the closest science race of the three games: Rome had 63 techs to Opus's 67 and nearly matched its science per turn, and three AI civs had started the space race. Opus finished last on score with 6 cities, its fewest so far, and won anyway. It ran three spaceports in parallel (Uruk, Eridu and Nippur) and bought Wernher von Braun, the Great Engineer who speeds up space projects, for the last one. Alliances with America and Rome kept it out of wars; Egypt parked artillery near Nippur but never declared war.

## Compared with games 1 and 2

| | Game 1 (playbook) | Game 2 (rules only) | Game 3 (playbook, Science goal) |
|---|---|---|---|
| Speed (turn limit) | Quick (330) | Quick (330) | Online (250) |
| Result | Science victory, turn 262 | Science victory, turn 266 | Science victory, turn 213 |
| Share of the turn limit used | 79% | 81% | 85% |
| Cost | $67.83 | $72.32 | $56.43 |
| Median seconds per turn | 47 | 53 | 53 |
| Tech lead over the best AI | -4 to +10, +7 at the end | -5 to +13, +9 at the end | -6 to +9, +4 at the end |
| Lead stays above zero from | turn 147 | turn 172 | turn 127 |
| Median length of the five reflections per turn | 283 characters | 140 characters | 312 characters |

Online speed makes everything cheaper in turns, so the turn numbers don't compare directly across speeds. As a share of the limit, the Science goal didn't make the win earlier. It made the path more direct: fewer cities, an earlier tech lead, and the space projects in three cities at once. The cost per turn ($0.26) matched game 1's.

## Cost and pace over the game

| Turns | API-equivalent $ | Median seconds per turn | Requests per turn |
|---|---|---|---|
| 1-50 | 6.71 | 38 | 4.3 |
| 51-100 | 16.60 | 84 | 6.2 |
| 101-150 | 14.80 | 52 | 5.3 |
| 151-200 | 16.15 | 58 | 5.6 |
| 201-213 | 2.17 | 42 | 3.1 |

## Harness

No stalls and no interventions: the fixes from games 1 and 2 held (the `end_turn` guard, the keep-awake task, repeatable Future Tech). The run waited a few minutes for a free headless slot on the shared dev server before turn 1. That wait isn't in the turn times.

Opus's own notes on what cost it along the way: Great People it couldn't use (they needed districts it never built), policy slots that kept emptying and needed refilling nearly every turn, and losing suzerainty of Buenos Aires twice.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and every city.
- [`shots/`](shots/): the screens at the start of turns 50, 130, 200 and the end (game window on top, war room below).
