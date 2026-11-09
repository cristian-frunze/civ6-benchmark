# Game 6: Sonnet 5.5 vs the built-in AI, goal: Science victory, Online speed

**Result: Science victory on turn 223.** Sonnet 5.5 (high effort) played Sumeria (Gilgamesh) in game 3's exact setup: the same 7 built-in AI civs on Prince, the same standard Pangaea map and start (same seed), Online speed, 250-turn limit, base game, playbook, Science goal. The only change is the model. It won 11 turns later than Opus did in game 3.

civ6-mcp announced the end as a "Score victory". It was a Science victory: a Score victory needs the turn limit (250), and the agent's fifth space project, Mars Habitation, was due that turn (its turn-222 note: "Habitation 2 turns left. 4/5 VP; victory ~T224"). When a space race ends, the game does not count the last project yet. civ6-mcp's science test then sees 4 of 5 and falls back to Score. In game 5 the same check said "Score" first and "Technology" 39 seconds later. `windows/bench_compat.py` now names a win before the turn limit by a civ one project short a Science victory.

| | |
|---|---|
| Played | 2026-11-08 13:45 to 19:05 CET, 5.3 hours wall clock |
| Turns | 223 (median 54 s per turn) |
| API-equivalent cost | **$58.70** at list prices (Sonnet 5.5: $2 / $10 per MTok in / out, $0.20 cache read, $4 cache write with the 1-hour TTL) |
| Tokens | 359K output, 249M cache read, 1.31M cache write, 2.6K uncached input |
| API requests | 1,294 (about 5.8 per turn) |
| Tool calls | 1,998, of which 7 returned errors |
| Claude Code sessions | 1: the whole game in one conversation, with no usage limits or interventions |

Sonnet's tokens cost half of Opus's, but its cache reads cost the same ($0.20 per MTok), and they are 85% of the bill ($49.85). It made 16% more requests than Opus in game 3 over a game 5% longer, so the two cost about the same.

## Final standings (turn 223)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Greece | 544 | 10 | 107 | 60 | 51 | 1,161 | 0 |
| Egypt | 454 | 7 | 172 | 57 | 50 | 860 | 1 |
| **Sumeria (Sonnet 5.5)** | **433** | 8 | **435** | **68** | 31 | 659 | **4, then 5** |
| America | 410 | 10 | 87 | 45 | 41 | 536 | 0 |
| Brazil | 407 | 5 | 66 | 42 | 43 | 105 | 0 |
| Germany | 388 | 8 | 86 | 42 | 36 | 348 | 0 |
| Rome | 367 | 6 | 147 | 57 | 38 | 841 | 1 |
| Spain | 262 | 5 | 96 | 43 | 29 | 683 | 0 |

## Compared with game 3 (Opus 5.5, same setup)

| | Game 3 (Opus 5.5) | Game 6 (Sonnet 5.5) |
|---|---|---|
| Result | Science victory, turn 212 | Science victory, turn 223 |
| Turn 50: score / cities / techs | 83 / 5 / 11 | 66 / 4 / 11 |
| Turn 100: score / cities / science / techs | 185 / 6 / 66 / 27 | 176 / 7 / 67 / 23 |
| Turn 150: score / cities / science / techs | 293 / 6 / 216 / 44 | 283 / 8 / 163 / 39 |
| Turn 200: score / science / techs | 387 / 297 / 63 | 382 / 410 / 62 |
| Tech lead over the best AI at turn 200 | +6 | +7 |
| Space projects done (turn reached) | 2 (183), 3 (201), 4 (205), 5 (212) | 1 (185), 2 (197), 3 (208), 4 (217), 5 (223) |
| Final score and rank | 400, 8th of 8 | 433, 3rd of 8 |
| Cost | $56.43 | $58.70 |
| Requests per turn | 5.2 | 5.8 |
| Wall clock | 4.6 h | 5.3 h |

Sonnet trailed Opus by 4 to 5 techs through the middle of the game, built more cities (8 to 6) and caught up on science late: by turn 200 it made 410 science per turn to Opus's 297. Barbarians and raiders it never saw killed at least six of its builders between turns 85 and 195.

## A harness trap, measured

Sonnet wrote that it had a "dead turn" 48 times, which it explained as "after each real turn, the next end_turn yields a dead state; just end_turn again". The tool log shows the cause. An AI civ often opens a diplomacy proposal during the AI turn. civ6-mcp's `end_turn` then stops with "Turn paused ... Use respond_to_diplomacy to handle it, then end_turn again". Once answered, the AI turn finishes and the agent's next turn has already begun. Its next `end_turn` call then ends that new turn. On turn 84, for example, Sonnet answered Spain, set one city's production, skipped all 16 units and ended the turn without playing it.

How often an agent ended a whole turn with no unit order this way:

| Game | Diplomacy pauses | Game had moved to the next turn | Next turn ended with no unit order |
|---|---|---|---|
| 1 (Opus, playbook) | 59 | 12 | 5 |
| 2 (Opus, rules only) | 88 | 32 | 11 |
| 3 (Opus, Science goal) | 53 | 16 | 3 |
| 4 (Opus, Domination goal) | 37 | 8 | 1 |
| 5 (Opus, Deity) | 38 | 9 | 0 |
| **6 (Sonnet 5.5)** | 68 | 34 | **8** |
| 7 (Opus, game 3 repeated) | 63 | 8 | 1 |
| 8 (Opus medium effort, fixed harness) | 60 | 11 | 0 |

It cost Sonnet about 8 of 223 turns and Opus 0 to 11 per game. (The first count read civ6-mcp's report of a turn end still in flight, "Turn N -> N+1" after the pause, as the end of the new turn, and gave 6, 14 and 9 for games 1, 2 and 6.) Game 7 still runs on this harness, to repeat game 3 exactly. From game 8 on, `windows/civ_mcp_http.py` fixes it: with an end-turn request in flight it skips civ6-mcp's blocker check, so `end_turn` reports the turn change and says the new turn is open, and after the agent answers a session the AI civs were waiting on, the first `end_turn` of a turn it has not touched is refused once. Game 10 repeats game 3 on the fixed harness, as the baseline for games 8 and 9.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 130 and 200 and at the end (game window on top, war room below).
