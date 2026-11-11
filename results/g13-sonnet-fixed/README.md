# Game 13: game 6 repeated on the fixed harness (Sonnet 5.5, high effort), goal: Science victory, Online speed

**Result: Science victory on turn 219**, 4 turns earlier than game 6. Game 13 is game 6 run again: Sonnet 5.5 at high effort playing Sumeria (Gilgamesh), against the same 7 built-in AI civs on Prince, on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. The change is the harness: game 11's, plus the spy-mission fix (5379f94), which game 11 found missing. With games 10 to 12 it puts every model on one harness. The fifth space project finished as turn 219 ended. Greece had three projects from turn 195 on and finished no more.

| | |
|---|---|
| Played | 2026-11-10 18:02 to 2026-11-11 02:07 CET, 8.1 hours wall clock, about 25 minutes of it in two AI-turn hangs |
| Turns | 219 (median 75 s per turn) |
| API-equivalent cost | **$62.17** at list prices (Sonnet 5.5: $2 / $10 per MTok in / out, $0.20 cache read, $4 cache write with the 1-hour TTL) |
| Tokens | 412K output, 262M cache read, 1.43M cache write, 2.7K uncached input |
| API requests | 1,339 (about 6.1 per turn) |
| Tool calls | 2,165, of which 1 returned an error (`ECONNRESET`, see game 12) |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 4 times |

Cache reads are 84% of the bill ($52.32). Output was $4.12 and cache writes $5.72.

## Final standings (turn 219)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Germany | 536 | 12 | 112 | 45 | 34 | 817 | 0 |
| **Sumeria (Sonnet 5.5)** | **513** | **14** | **263** | **68** | 36 | 489 | **4, then 5** |
| Rome | 470 | 13 | 129 | 48 | 40 | 894 | 0 |
| Egypt | 435 | 9 | 93 | 46 | 50 | 1011 | 0 |
| Greece | 427 | 11 | 240 | 60 | 38 | 966 | 3 |
| Spain | 422 | 8 | 139 | 45 | 44 | 656 | 0 |
| America | 377 | 9 | 76 | 45 | 36 | 1009 | 0 |
| Brazil | 307 | 4 | 30 | 38 | 37 | 87 | 0 |

## The space race and the spies

Greece started first: its projects came on turns 164, 177 and 195, while Sumeria's first came on 187. On turn 195 Sonnet wrote "ALERT: Greece 3/5 projects ... sabotage Greek spaceports with DISRUPT_ROCKETRY". This is the mission game 11's agent asked for and the harness did not have. Here `get_spies` offered it in Greek cities building a space project, and Sonnet launched it four times: at Argos on turns 196, 198 and 203, and at Sparta on turn 210. Two spies were killed, one during the first Argos mission and one on its way to another Greek city. The turn-203 mission worked: the report for turn 205 says "Success Disrupting Rocketry", and on turn 207 the agent noted that Argos was no longer building a project. Greece finished no project after turn 195. Sumeria's second and third came on turn 206 (the Moon Landing, and the Mars Reactor, which the Great Scientist Carl Sagan finished with his 1,500 production), the fourth on 218 and the fifth as 219 ended. So the mission now works, an agent reaches for it, and it set Greece back at least once. Whether it is why Greece stopped at three cannot be told from one game.

## All four models on one harness

| | Game 10 (Opus 5.5) | Game 11 (Fable 5.1) | Game 12 (Fable 5.2) | Game 13 (Sonnet 5.5) |
|---|---|---|---|---|
| Result | Science victory, turn 200 | Defeat, turn 209 (Greece) | **Science victory, turn 170** | Science victory, turn 219 |
| Turn 100: score / cities / science / techs | 233 / 8 / 137 / 31 | 196 / 7 / 78 / 31 | 187 / 5 / 98 / 31 | 176 / 8 / 65 / 23 |
| Turn 150: score / cities / science / techs | 346 / 8 / 226 / 48 | 350 / 11 / 180 / 45 | 365 / 7 / 332 / 56 | 315 / 13 / 148 / 34 |
| Tech lead over the best AI at turns 100 / 150 / 200 | +1 / +7 / +6 | -4 / -5 / +2 | -1 / +13 / won at 170 | -9 / -9 / +11 |
| First space project | 161 | 175 | 151 | 187 |
| Final score and rank | 446, 2nd of 8 | 548, 2nd of 8 | 417, 2nd of 8 | 513, 2nd of 8 |
| Cost | $58.24 | $106.37 | $91.67 | $62.17 |
| Cost per turn | $0.291 | $0.509 | $0.539 | $0.284 |
| Requests per turn | 5.5 | 4.0 | 6.1 | 6.1 |
| Wall clock (median per turn) | 5.5 h (62 s) | 6.7 h (94 s) | 6.5 h (104 s) | 8.1 h (75 s) |

Games 11 and 12 ran on the same harness. Game 10 ran one fix earlier, without the turn snapshot fix (730ef83), so 42 of its 200 turn reports lost their events; game 13 ran one fix later, with the two missing spy missions. One game per model is a small sample: games 9 and 11, the same model and setup, ended in a win on turn 203 and a defeat on turn 209.

## Compared with game 6 (Sonnet 5.5, old harness)

| | Game 6 | Game 13 |
|---|---|---|
| Result | Science victory, turn 223 | Science victory, turn 219 |
| Turn 50: score / cities / techs | 66 / 4 / 11 | 72 / 4 / 10 |
| Turn 100: score / cities / science / techs | 176 / 7 / 67 / 23 | 176 / 8 / 65 / 23 |
| Turn 150: score / cities / science / techs | 283 / 8 / 163 / 39 | 315 / 13 / 148 / 34 |
| Turn 200: score / science / techs | 382 / 410 / 62 | 463 / 372 / 66 |
| Tech lead over the best AI at turns 100 / 150 / 200 | -10 / -5 / +7 | -9 / -9 / +11 |
| Space projects done (turn reached) | 1 (185), 2 (197), 3 (208), 4 (217), 5 (223) | 1 (187), 2 and 3 (206), 4 (218), 5 (219) |
| Best AI's space projects | 1 | 3 (Greece) |
| Final score and rank | 433, 3rd of 8 | 513, 2nd of 8 |
| Cost | $58.70 | $62.17 |
| Requests per turn | 5.8 | 6.1 |
| Output tokens / thinking characters | 359K / 246K | 412K / 285K |
| Wall clock (median per turn) | 5.3 h (54 s) | 8.1 h (75 s) |

The two Sonnet games ran close to each other: the same score at turn 100, the same tech counts, and a win 4 turns apart. Game 13 grew wider (14 cities against 8) and faced a stronger Greece.

## The harness in this game

From the server log and the agent's tool results:

- **Two AI-turn hangs, both on turn 108**, about 25 minutes in all. An AI trade deal was still pending when `end_turn` sent the turn end: the server logged "incoming trade deal pending, use get_pending_trades" before the turn end and again at the 10-minute timeout. civ6-mcp reloaded the turn, the AI offered again, and the turn hung a second time before it went through. This differs from game 12's hangs, which came after the agent's own accepted proposals. Sonnet proposed no trades and answered 35 AI deals. Replayed live from the turn's autosave after the game, it hung again, but no deal was pending then: the leader screen was up with no session behind it, after the agent accepted Rome's alliance offer and answered Germany's greeting while the AI turns were paused, and Brazil's turn waited behind the screen's lock. From game 14, `end_turn` closes such a screen once the AI turns have been quiet for 45 s; the replayed turn then ended in 100 s ([setup](../../docs/setup.md)).
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 67 pauses; 43 times the game had moved to the next turn, and 7 of those turns ended with no unit order (game 6: 6). On each of the 7, Sonnet set research or production and skipped its units (it called `skip_remaining_units` 189 times in the game); it read the game state first on 5 of them. That is its way of playing a quiet turn, not the blind end of an unplayed turn the fix from game 8 removed. The script cannot tell the two apart.
- **Turn reports kept their events**: the turn snapshot failed 0 times. One `ECONNRESET` (the keep-alive race found in game 12; its fix loads from game 14).
- **Moves** said "arrived with no moves left" 111 times; 17 `improve` orders were refused for lack of moves. **Move-and-attack** results were read again 7 times, **auto-explore** was sent again 17 times, `skip_remaining_units` left units with orders of their own alone 208 times, and the harness closed a diplomacy screen left open 18 times. `NO_SESSION` came up 3 times, each naming the open session or saying none was open. `SILENT_FAILURE` and `InvitePopup` never came up.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. The last row (turn 220) is the agent's closing summary after the victory.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 130, 200 and 219 (game window on top, war room below).
