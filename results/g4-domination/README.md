# Game 4: Opus 5.5 vs the built-in AI, goal: Domination victory, Online speed

**Result: Domination victory on turn 169.** Opus 5.5 (high effort) played Sumeria (Gilgamesh) against the same 7 built-in AI civs on Prince, on the same standard Pangaea map and start as game 3 (same seed, Online speed, 250-turn limit), base game, with the playbook. The only change from game 3 is the goal named in the system prompt: a Domination victory. Every victory type stayed on for every civ. It took the last original capital, Rome, on turn 169, 81 turns before the limit and 43 turns earlier than game 3's science win.

| | |
|---|---|
| Played | 2026-11-07, 7.6 hours wall clock |
| Turns | 169 (median 125 s per turn) |
| API-equivalent cost | **$100.64** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 645K output, 350M cache read, 2.22M cache write, 3.7K uncached input |
| API requests | 1,839 (about 10.8 per turn) |
| Tool calls | 2,526, of which 9 returned errors |
| Claude Code sessions | 1: the whole game in one conversation, with no usage limits |

Cache reads are most of the bill again ($69.95). Output was $12.89 and cache writes $17.79.

civ6-mcp announced the end as a "Culture victory". It was a Domination victory: the game showed the domination cinematic (a military parade), every rival had lost its original capital, and Opus had 5 or 6 visiting tourists against each rival's 19 to 110 domestic ones, nowhere near a culture win. civ6-mcp names the victory with fallback tests. Its domination test calls an API the base game lacks, so it failed, and its culture test then misfired. `windows/bench_compat.py` now fixes both tests for later games.

## How it went

| Turn | Original capital taken |
|---|---|
| 42 | Madrid (Spain) |
| 57 | Rio de Janeiro (Brazil) |
| 72 | Memphis (Egypt) |
| 130 | Sparta (Greece) |
| 141 | Washington (America) |
| 151 | Aachen (Germany) |
| 169 | Rome (Rome) |

Opus opened with Sumeria's war carts, which need no tech, and took two capitals before turn 60. It finished Spain off on turn 101 (Barcelona was Spain's last city). The middle game was a long build-up: from turn 100 to turn 140 its military strength went from about 1,100 to 2,350 and its city count from 15 to 26. Then came artillery, tanks and battering rams. It took 22 cities in all, 20 from the AI civs and the city-states Buenos Aires and Mogadishu, and kept every one. At the end it had 34 cities and a military strength of 2,880, six times Rome's 461. It also ended with the biggest tech lead of any game so far: 62 techs to Rome's 44 (+18), against game 3's +4 when it was aiming at science.

## Final standings (after Rome fell)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| **Sumeria (Opus 5.5)** | **930** | **34** | **298** | **62** | **40** | **2,880** |
| Rome | 426 | 10 | 66 | 44 | 35 | 461 |
| Greece | 231 | 2 | 19 | 41 | 28 | 274 |
| America | 217 | 4 | 65 | 33 | 24 | 50 |
| Brazil | 185 | 3 | 26 | 31 | 24 | 48 |
| Germany | 178 | 3 | 18 | 30 | 26 | 159 |
| Egypt | 178 | 4 | 22 | 31 | 21 | 112 |
| Spain | eliminated on turn 101 | | | | | |

## Compared with game 3

| | Game 3 (Science goal) | Game 4 (Domination goal) |
|---|---|---|
| Result | Science victory, turn 212 | Domination victory, turn 169 |
| Share of the 250-turn limit used | 85% | 68% |
| Cost | $56.43 | $100.64 |
| Cost per turn | $0.26 | $0.59 |
| Median seconds per turn | 53 | 125 |
| Requests per turn | 5.2 | 10.8 |
| Cities at the end | 6 | 34 |
| Score at the end | 400, last of 8 | 930, more than twice the next civ |
| Median length of the five reflections per turn | 312 characters | 67 characters |

Same map, same start, same opponents: the named goal changed everything about how Opus played. A domination game costs more per turn because every unit needs orders: Opus averaged 16 requests per turn from turn 101 to 150, and on its last turn it still had 110 units to skip. Its turn notes got short ("See prior.") as the army grew.

## Cost and pace over the game

| Turns | API-equivalent $ | Median seconds per turn | Requests per turn |
|---|---|---|---|
| 1-50 | 12.65 | 64 | 6.5 |
| 51-100 | 29.04 | 138 | 9.9 |
| 101-150 | 46.87 | 170 | 16.0 |
| 151-169 (and two rows after the end) | 12.08 | 162 | 10.4 |

## Harness incidents and interventions

- **Turn 58: an AI turn waited 20 minutes on a diplomacy screen.** At the end of turn 58, civ6-mcp auto-dismissed Brazil's war declaration and told the agent the turn had not advanced. The AI turn was in fact still running, and America then opened a diplomacy session (a delegation offer) that waited for an answer. The `end_turn` guard in `windows/civ_mcp_http.py` only waited for the player's turn, so nothing told the agent about the session. Opus called `end_turn` four more times, then reloaded the turn's save itself and replayed turn 58 ($0.81 and 30 minutes for that turn). We fixed the guard: while the AI civs move, it now checks once on entry and once at 45 seconds for an open session, and tells the agent to answer it. We restarted the server with the fix on turn 61, triggered by an `end_turn` that had just returned (about 25 seconds down). The `end_turn` the agent sent during the restart failed with a connection error, and its retry got the new message about Brazil's open peace offer, which it accepted.
- **Turn 169: the victory was named wrong** (above). Nothing to change in the game.

Everything done to the game from outside the agent is in [interventions.jsonl](interventions.jsonl). None of it changed the game state; the turn 58 reload was the agent's own call.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Rows 170 and 171 are the calls after the game ended.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 100 and 140 and at the end (game window on top, war room below).
- [`interventions.jsonl`](interventions.jsonl): every action on the running game from outside the agent.
