# Game 14: game 12 again (Fable 5.2, high effort), goal: Science victory, Online speed

**Result: Science victory on turn 168, first in score.** Game 14 repeats game 12 to see whether its result holds: Fable 5.2 at high effort playing Sumeria (Gilgamesh), against the same 7 built-in AI civs on Prince, on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. The one change is the harness: the trade tools wait for the AI's answer, end turn closes a leader screen left up while the AI turns wait, and the server keeps idle connections open for an hour (fixes for what went wrong in games 12 and 13). Game 12 won on turn 170, 2nd in score. The fifth space project finished as turn 168 ended, and no AI civ had started one.

| | |
|---|---|
| Played | 2026-11-11 04:26 to 10:09 CET, 5.7 hours wall clock, with no AI-turn hangs |
| Turns | 168 (median 105 s per turn) |
| API-equivalent cost | **$79.27** at list prices (Fable 5.2: $8 / $40 per MTok in / out, $0.20 cache read, $16 cache write with the 1-hour TTL). At Fable 5.1's prices the same tokens would cost $99.09 |
| Tokens | 472K output, 184M cache read, 1.48M cache write, 1.9K uncached input |
| API requests | 948 (about 5.6 per turn) |
| Tool calls | 1,261, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 4 times |

Cache reads are 46% of the bill ($36.76), cache writes 30% ($23.63) and output 24% ($18.86). By 50-turn range the game cost $10.50, $27.18, $33.11 and $8.48 (turns 151 to 168).

## Final standings (turn 168)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| **Sumeria (Fable 5.2)** | **471** | **9** | **396** | **64** | 36 | **624** | **4, then 5** |
| Brazil | 352 | 8 | 113 | 41 | 31 | 145 | 0 |
| Rome | 350 | 7 | 102 | 43 | 38 | 259 | 0 |
| Egypt | 336 | 7 | 71 | 39 | 35 | 488 | 0 |
| Germany | 303 | 9 | 64 | 31 | 23 | 422 | 0 |
| Spain | 296 | 6 | 120 | 41 | 29 | 560 | 0 |
| America | 283 | 7 | 45 | 35 | 32 | 197 | 0 |
| Greece | 263 | 6 | 71 | 41 | 25 | 152 | 0 |

## How it went

This time Fable 5.2 expanded early: 5 cities at turn 50 and 7 at turn 70 (game 12 had 5 at turn 100), then 8 at turn 103 and 9 by turn 120. Its science per turn was the highest of any civ from turn 54 on, and it led in score from turn 68 on. It made friends with Rome, Spain and Egypt by turn 59 and allied with all three by turn 72. Those alliances pulled it into wars it did not declare: Brazil and America were at war with it from turn 93 to turn 103 and again from about turn 115 to turn 130, and Rome and America from turn 159 to the end. None of them reached its land. On turn 131 it turned down an alliance with Rome because "alliances pull me into wars". The fighting at home was with barbarians: a camp southwest of Isin sent Men-at-Arms and a Musketman that pillaged districts in Isin and Uruk and plundered two traders between turns 108 and 129, until city strikes, crossbows and cannons killed them. Its tech lead over the best AI was 3 at turn 100, 15 at turn 150 and 21 at the end. The space projects came on turns 146 (Earth Satellite), 155 (Moon Landing), 163 (Mars Habitation), 166 (Hydroponics) and 168, when the agent used the great person Carl Sagan on the Mars Reactor in Kish and the project finished at once, as in game 12.

## Compared with game 12 and games 9 to 11

| | Game 9 (Fable 5.1, old harness) | Game 10 (Opus 5.5) | Game 11 (Fable 5.1) | Game 12 (Fable 5.2) | Game 14 (Fable 5.2) |
|---|---|---|---|---|---|
| Result | Science victory, turn 203 | Science victory, turn 200 | Defeat, turn 209 | Science victory, turn 170 | **Science victory, turn 168** |
| Turn 50: score / cities / techs | 66 / 4 / 9 | 77 / 4 / 14 | 80 / 4 / 12 | 80 / 4 / 13 | 81 / 5 / 13 |
| Turn 100: score / cities / science / techs | 197 / 6 / 71 / 28 | 233 / 8 / 137 / 31 | 196 / 7 / 78 / 31 | 187 / 5 / 98 / 31 | **239** / 7 / 133 / 31 |
| Turn 150: score / cities / science / techs | 321 / 7 / 233 / 48 | 346 / 8 / 226 / 48 | 350 / 11 / 180 / 45 | 365 / 7 / **332** / **56** | **430** / 9 / 298 / **56** |
| Tech lead over the best AI at turns 100 / 150 | -3 / +8 | +1 / +7 | -4 / -5 | -1 / +13 (+18 at turn 170) | **+3 / +15** (+21 at turn 168) |
| Space projects done (turn reached) | 1 (168), 2 (182), 3 (193), 4 (194), 5 (203) | 1 (161), 2 (179), 3 (184), 4 and 5 (200) | 1 (175), 2 (191), 3 (207), 4 (208) | 1 (151), 2 (161), 3 (169), 4 and 5 (170) | 1 (146), 2 (155), 3 (163), 4 (166), 5 (168) |
| Best AI's space projects | 1 | 2 | 5 (Greece won) | 0 | 0 |
| Final score and rank | 428, 4th of 8 | 446, 2nd of 8 | 548, 2nd of 8 | 417, 2nd of 8 | **471, 1st of 8** |
| Cost | $102.47 | $58.24 | $106.37 | $91.67 | $79.27 |
| Cost per turn | $0.505 | $0.291 | $0.509 | $0.539 | $0.472 |
| Requests per turn | 4.5 | 5.5 | 4.0 | 6.1 | 5.6 |
| Output tokens / thinking characters | 468K / 304K | 323K / 215K | 602K / 365K | 564K / 387K | 472K / 322K |
| Wall clock (median per turn) | 6.0 h of play (84 s) | 5.5 h (62 s) | 6.7 h (94 s) | 6.5 h (104 s) | 5.7 h (105 s) |

The repeat held: Fable 5.2 won both of its games on turns 168 and 170, 30 or more turns before any other model's win on this setup, and no AI built a space project in either. The two games took different paths to the same turn. Game 12 stayed at 5 cities until turn 100 and pulled ahead on science after it; game 14 settled faster, led in score from turn 68 and was ahead on techs by turn 100. Game 14 finished first in score where game 12 was second to Egypt. It cost $12 less than game 12 for two fewer turns, with fewer requests and output tokens per turn. Two runs are a small sample, but Fable 5.1's two games on this setup split a win on turn 203 and a loss on turn 209, while Fable 5.2's two ended 2 turns apart.

## The harness in this game

From the server log and the agent's tool results:

- **No AI-turn hangs.** Game 12 had three (turns 96, 120 and 143), each costing about 13 minutes and undoing the turn. Game 14 sent 11 trade proposals on 4 turns (107, 112, 131 and 132; 3 accepted, 7 rejected and 1 with no answer), tested 12 more on turn 107, and answered 27 AI offers (13 accepted, 14 rejected). Every trade turn ended normally.
- **No tool errors.** Game 12 had 8 `ECONNRESET` failures from uvicorn's 5-second keep-alive timeout; with idle connections kept an hour (46c0e13) there were none.
- **Two end turns were refused for about 10 minutes each**, on turns 100 and 101. As the turn ended, the game moved units along their orders and one of them then needed new orders, so the game held the turn while civ6-mcp waited for the AI turns. Games 2 to 14 had 28 such waits, 15 of them in game 13. From game 15 on, `end_turn` notices it at 45 s and names the unit (a692ba5).
- **The trade test said yes where Rome meant no.** On turn 107 the agent tested Coffee for 4, 8, 14, 22 and 30 gold per turn from Rome and got "ACCEPTABLE, this deal would be accepted as-is" each time. Rome then refused it at 20 and at 8, and America took it for 5. Replayed live from the turn's autosave, Rome answered the test's "what would make this work" (EQUALIZE) by giving the terms back unchanged at every price, even 30 gold per turn or 60 gold, and civ6-mcp read unchanged terms as acceptable. The deal screen's own check (INSPECT, whose answer decides whether it offers Accept) told the prices apart: America would pay up to 4 gold per turn for Coffee and Rome up to 5 for Tea, and proposals at the check's limit (America's Coffee at 4, Rome's Citrus at 3) were accepted outright. Its no is strict: Rome also took Tea at 6, and Spain Truffles at 1, as an `ADJUSTED` answer that kept the terms, but refused Coffee at 4. From game 15 a test whose terms come back unchanged asks that check too and reports `NOT ACCEPTABLE as-is` when it says no.
- **Leader screens**: the harness closed a leader screen left open after a diplomacy answer 40 times. The new end-turn check never had to close one while the AI turns waited.
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 54 pauses; 39 times the game had already moved to the next turn, and 1 of those turns ended with no unit order.
- **Moves** said "arrived with no moves left" 72 times. **Move-and-attack** left 1 `STOPPED_SHORT`. **Auto-explore** was sent again 35 times, and `skip_remaining_units` left units with orders of their own alone 32 times.
- `NO_SESSION`, `SILENT_FAILURE` and `InvitePopup` never came up. Fable 5.2 sent no spy orders.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 169 is the agent's closing summary after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 168 (game window on top, war room below).
