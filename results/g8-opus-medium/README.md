# Game 8: Opus 5.5 at medium effort vs the built-in AI, goal: Science victory, Online speed

**Result: Science victory on turn 224.** Game 3's setup with one change to the agent: Opus 5.5 at **medium** effort (Claude Code's default) instead of high. Same civ (Sumeria, Gilgamesh), the same 7 built-in AI civs on Prince, the same standard Pangaea map and start (same seed), Online speed, 250-turn limit, base game, playbook and Science goal. It is also the first game on the fixed harness: `end_turn` reports the new turn after a diplomacy pause, and menu loads raise the game window (see [setup](../../docs/setup.md)). Game 3 won on turn 212 and game 7, its repeat, on turn 206. This one won on turn 224, with Greece one space project behind.

| | |
|---|---|
| Played | 2026-11-09 02:25 to 11:04 CET, 8.6 hours wall clock, of which 3.8 hours went to 18 AI-turn hangs (below) |
| Turns | 224 (median 52 s per turn) |
| API-equivalent cost | **$54.83** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 321K output, 198M cache read, 1.11M cache write, 2.2K uncached input |
| API requests | 1,112 (about 4.9 per turn) |
| Tool calls | 1,650, of which 5 returned errors |
| Claude Code sessions | 1, no usage limits. Three interventions, all before the agent started: the first two starts failed to load the start save ([`interventions.jsonl`](interventions.jsonl)) |

Cache reads are 72% of the bill ($39.50). Output was $6.41 and cache writes $8.90.

## Final standings (turn 224)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Egypt | 555 | 12 | 272 | 63 | 41 | 579 | 0 |
| Greece | 499 | 13 | 248 | 67 | 37 | 602 | **4** |
| Rome | 482 | 12 | 128 | 49 | 51 | 472 | 0 |
| **Sumeria (Opus 5.5, medium)** | **453** | 8 | **247** | **68** | 38 | 216 | **4, then 5** |
| Brazil | 424 | 8 | 102 | 47 | 37 | 156 | 0 |
| Spain | 384 | 8 | 151 | 46 | 37 | 560 | 0 |
| America | 348 | 8 | 82 | 43 | 35 | 466 | 0 |
| Germany | 270 | 7 | 35 | 33 | 29 | 635 | 0 |

## Compared with games 3 and 7 (same setup, high effort)

| | Game 3 | Game 7 | Game 8 (medium) |
|---|---|---|---|
| Result | Science victory, turn 212 | Science victory, turn 206 | Science victory, turn 224 |
| Turn 50: score / cities / techs | 83 / 5 / 11 | 83 / 4 / 12 | 77 / 4 / 11 |
| Turn 100: score / cities / science / techs | 185 / 6 / 66 / 27 | 207 / 8 / 87 / 26 | 212 / 7 / 106 / 33 |
| Turn 150: score / cities / science / techs | 293 / 6 / 216 / 44 | 339 / 8 / 210 / 47 | 333 / 8 / 259 / 53 |
| Turn 200: score / science / techs | 387 / 297 / 63 | 418 / 306 / 65 | 421 / 218 / 68 |
| Tech lead over the best AI at turns 100 / 150 / 200 | -4 / +3 / +6 | -7 / +3 / +5 | **+2 / +9 / +9** |
| Space projects done (turn reached) | 2 (183), 3 (201), 4 (205), 5 (212) | 2 (174), 3 (190), 4 (193), 5 (206) | 1 (179), 2 (201), 3 (220), 4 and 5 (224) |
| Final score and rank | 400, 8th of 8 | 422, 6th of 8 | 453, 4th of 8 |
| Cost | $56.43 | $62.87 | $54.83 |
| Cost per turn | $0.265 | $0.304 | $0.245 |
| Requests per turn | 5.2 | 5.7 | 4.9 |
| Output tokens / thinking characters | 331K / 206K | 339K / 212K | 321K / 195K |
| Wall clock | 4.6 h | 6.6 h | 8.6 h (4.8 h without the hangs) |

Medium effort changed little about how much Opus thought or spent: 3 to 8% less output and thinking than the two high-effort games and 8 to 19% less per turn, so with more turns the bill came out about the same. The game itself went differently. Game 8 led the AI in techs from turn 100 on, by 9 at turns 150 and 200, where games 3 and 7 never led by more than 6. It still won 12 to 18 turns later, because it turned that lead into space projects slowly: its first came on turn 179 and the next three took until turn 224. From turn 205 it ran out of gold ("Gold 0, -46/t (bankrupt; units being disbanded)", turn 210, with 128 gold of maintenance a turn against 99 of income), science fell from 259 at turn 150 to 91 at turn 213, and Greece drew level at 3 and then 4 projects. With one game per setting and a 6-turn spread between games 3 and 7, this says medium effort saves little; it doesn't show that it plays worse.

## AI-turn hangs

civ6-mcp gives up on an end turn after about 10 minutes with no turn change ("AI turn processing appears stuck"), reloads the save from the start of that turn, and ends the turn again. Game 8 hit this 18 times, far more than any earlier game (1 to 4), and lost 3.8 hours to it. Both causes were found after the game, and the fixes are in from game 10 on (see [setup](../../docs/setup.md)):

- **Turns 12 and 13, 11 hangs, 2.4 hours: Spain's first greeting.** Spain greeted the player while turn 13 was ending. civ6-mcp reported "Turn paused" and, after the answer, kept waiting on its end-turn request, but the turn never ended: the greeting had, by all the evidence, cancelled the request. In game 7, which met the same greeting on turn 20, the end turn sent after answering it ended the turn in 25 seconds. Each reload brought back the same greeting. The agent noticed ("Spain first-contact dialog loops infinitely"), loaded turn 12 itself, moved its units elsewhere and met Spain later without trouble.
- **Turns 207 to 213, 7 hangs, 1.4 hours: trades.** The agent proposed its first trades on turn 207, and every turn in which it proposed one hung, whether the AI accepted or refused. The game's diplomacy screen locks the engine while it is open, and civ6-mcp hid it after a trade instead of closing it, so the lock stayed. In all eight games, 14 of the 23 end turns after a `propose_trade` hung, against 3 of 1,600 after turns with no diplomacy. Each reload undid the whole turn, including the trades the agent was making to get out of bankruptcy, and nothing told it so. It concluded the game was crashing, tested which action caused it ("Rollback happened when doing deletions+focus+deals in the same turn"), proposed no trade after turn 213, and rejected an AI's deal "avoiding deal-related crashes". The bankruptcy that slowed its science lasted through these turns.

## Diplomacy-pause trap

`tools/turn_trap.py`: 60 diplomacy pauses, 11 times the game had moved to the next turn before the agent's next `end_turn`, and **0** turns ended with no unit order (games 1 to 7: 0 to 8 per game). This is the first game on that fix.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`interventions.jsonl`](interventions.jsonl): what was done from outside the agent, all before it started.
- [`shots/`](shots/): the screens at the start of turns 50, 130 and 200 and at the end (game window on top, war room below).
