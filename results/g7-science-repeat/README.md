# Game 7: game 3 repeated, Opus 5.5 vs the built-in AI, goal: Science victory, Online speed

**Result: Science victory on turn 206.** A repeat of game 3, run to see how much one game varies from the next: same model (Opus 5.5, high effort), same civ (Sumeria, Gilgamesh), the same 7 built-in AI civs on Prince, the same standard Pangaea map and start (same seed), Online speed, 250-turn limit, base game, playbook, Science goal, and the same harness. Game 3 won on turn 212; this one won 6 turns earlier.

| | |
|---|---|
| Played | 2026-11-08 19:06 to 2026-11-09 01:46 CET, 6.6 hours wall clock, of which 67 minutes went to a game crash (below) |
| Turns | 206 (median 69 s per turn) |
| API-equivalent cost | **$62.87** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL), of which $5.25 was spent between the hang and getting past turn 102 |
| Tokens | 339K output, 226M cache read, 1.37M cache write, 2.3K uncached input |
| API requests | 1,172 (about 5.7 per turn) |
| Tool calls | 1,527, of which 5 returned errors |
| Claude Code sessions | 2 in one conversation (the second resumed the first, with its context), no usage limits or interventions |

Cache reads are 72% of the bill ($45.14). Output was $6.78 and cache writes $10.95.

## Final standings (turn 206)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Brazil | 506 | 9 | 136 | 46 | 50 | 582 | 0 |
| Rome | 488 | 12 | 188 | 56 | 43 | 276 | 0 |
| Spain | 475 | 9 | 230 | 52 | 49 | 804 | 0 |
| Greece | 429 | 11 | 301 | 62 | 28 | 1,113 | 1 |
| Egypt | 423 | 10 | 117 | 47 | 45 | 411 | 0 |
| **Sumeria (Opus 5.5)** | **422** | 8 | **310** | **65** | 36 | 618 | **4, then 5** |
| America | 418 | 10 | 88 | 42 | 42 | 447 | 0 |
| Germany | 295 | 8 | 64 | 37 | 30 | 601 | 0 |

## Compared with game 3 (same setup)

| | Game 3 | Game 7 |
|---|---|---|
| Result | Science victory, turn 212 | Science victory, turn 206 |
| Turn 50: score / cities / techs | 83 / 5 / 11 | 83 / 4 / 12 |
| Turn 100: score / cities / science / techs | 185 / 6 / 66 / 27 | 207 / 8 / 87 / 26 |
| Turn 150: score / cities / science / techs | 293 / 6 / 216 / 44 | 339 / 8 / 210 / 47 |
| Turn 200: score / science / techs | 387 / 297 / 63 | 418 / 306 / 65 |
| Tech lead over the best AI at turns 100 / 150 / 200 | -4 / +3 / +6 | -7 / +3 / +5 |
| Space projects done (turn reached) | 2 (183), 3 (201), 4 (205), 5 (212) | 2 (174), 3 (190), 4 (193), 5 (206) |
| Final score and rank | 400, 8th of 8 | 422, 6th of 8 |
| Cost | $56.43 | $62.87 ($57.62 without the crash) |
| Requests per turn | 5.2 | 5.7 |
| Wall clock | 4.6 h | 6.6 h (5.5 h without the crash) |

Game 7 settled two more cities (8 to 6) and was ahead of game 3 on score at turns 100, 150 and 200, but its tech count stayed within 3 of game 3's throughout. It reached 4 space projects 12 turns sooner, then took 13 turns for the last one, the Mars Reactor ("holding until it completes", turn 199). The two runs ended 6 turns apart, which gives a rough noise floor for comparing single games on this setup.

## The turn-102 crash

The end of turn 102 hung, and after 15 minutes Claude Code timed out the `end_turn` call. The game had dropped to the main menu. For about 30 minutes, every reload failed with "Could not find 'Load Game' button": `restart_and_load`, `load_game_save` and `load_save_from_menu` alike, on four saves. The PC's server log shows why. civ6-mcp clicks "Single Player" and then looks for "Load Game" by OCR for 5 seconds, but the click opened nothing, and OCR still read the main menu. The first session gave up and stopped. The runner resumed the same conversation, and a few attempts later a `restart_and_load` worked. Turn 102 then hung a second time, so the agent loaded the turn-101 autosave and replayed turns 101 and 102 with some choices changed ("to change RNG path"). The game went on normally from turn 103.

From game 8 on, `windows/civ_mcp_http.py` clicks "Single Player" again, up to 3 times, when "Load Game" does not appear.

## Diplomacy-pause trap

`tools/turn_trap.py`: 63 diplomacy pauses, 8 times the game had moved to the next turn before the agent's next `end_turn`, and 1 turn ended with no unit order (game 3: 53, 16 and 3). Game 7 is the last game on the old harness. From game 8 on, `end_turn` reports the new turn instead.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 130 and 200 and at the end (game window on top, war room below).
