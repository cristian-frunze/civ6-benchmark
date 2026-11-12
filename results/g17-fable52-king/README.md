# Game 17: Fable 5.2 on King, goal: Science victory, Online speed

**Result: Science victory on turn 170, first in score.** Game 17 puts Fable 5.2 (high effort) on King, one level above Prince, where it won games 12 and 14 (turns 170 and 168), and one below Emperor, where it lost game 16 (turn 174). Everything else is the same: Sumeria (Gilgamesh) against the same 7 built-in AI civs on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. The King start was made with `remote/make-start.sh` and differs from the others only in the difficulty. The last space project finished as turn 169 ended; Spain, the only other civ in the space race, had 2. The harness is game 16's, unchanged.

| | |
|---|---|
| Played | 2026-11-11 23:28 to 2026-11-12 04:46 CET, 5.3 hours wall clock, with no AI-turn hangs |
| Turns | 170 (median 88 s per turn) |
| API-equivalent cost | **$71.03** at list prices (Fable 5.2: $8 / $40 per MTok in / out, $0.20 cache read, $16 cache write with the 1-hour TTL). At Fable 5.1's prices the same tokens would cost $88.79 |
| Tokens | 394K output, 183M cache read, 1.17M cache write, 1.9K uncached input |
| API requests | 970 (about 5.7 per turn) |
| Tool calls | 1,176, one returned an error (a reply lost on the connection, below) |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 3 times |

Cache reads are 52% of the bill ($36.59), cache writes 26% ($18.67) and output 22% ($15.76). By 50-turn range the game cost $10.92, $23.20, $24.66 and $12.26 (turns 151 to 170, plus the closing summary).

## Final standings (turn 169)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| **Sumeria (Fable 5.2)** | **442** | 8 | **316** | **68** | 37 | **602** | **4, then 5** |
| Egypt | 400 | 8 | 91 | 44 | 43 | 505 | 0 |
| Brazil | 394 | 8 | 70 | 39 | 41 | 297 | 0 |
| America | 377 | **10** | 87 | 42 | 34 | 424 | 0 |
| Spain | 371 | 6 | 169 | 54 | **44** | 347 | 2 |
| Rome | 312 | 8 | 85 | 38 | 36 | 308 | 0 |
| Greece | 300 | 8 | 177 | 46 | 24 | 216 | 0 |
| Germany | 230 | 6 | 42 | 32 | 23 | 356 | 0 |

## How it went

No civ declared war on Fable 5.2 in this game; barbarians killed a Settler on turn 36, and it never lost a city. It had 2 cities at turn 25, 4 at turn 50 and 8 by turn 72, and kept all 8 to the end. At turn 50 it had 13 techs to the AI's 11 to 15; it had the highest science per turn of any civ from turn 71 on, though Spain still had 4 more techs at turn 100. It first led in score on turn 107 and traded the lead with Egypt until turn 126; from turn 125 it led in techs and from turn 126 in score, both to the end. Its tech lead over the best AI was 9 at turn 150 and 14 at the end. The space projects came in quick succession: Earth Satellite in Kish on turn 145, the Moon Landing on turn 157, Mars Hydroponics on turn 160 (finished at once by the great person Carl Sagan, as in games 12 and 14), the Mars Reactor in Uruk on turn 168 and Mars Habitation in Kish as turn 169 ended. Spain finished its first project on turn 153 and its second on turn 168. The agent made allies of Germany, Greece, Egypt and Brazil at different times, answered 19 AI offers (13 accepted), and spent its spies only on defense (3 counterspy missions).

## Fable 5.2 on four difficulty levels

| | Game 12 (Prince) | Game 14 (Prince) | **Game 17 (King)** | Game 16 (Emperor) | Game 15 (Deity) |
|---|---|---|---|---|---|
| Units each AI civ starts with | 2 | 2 | **3** | 4 | 6 |
| Result | Science victory, turn 170 | Science victory, turn 168 | **Science victory, turn 170** | Defeat, turn 174 (Greece) | Defeat, turn 132 (Greece) |
| Turn 50: score / cities / techs | 80 / 4 / 13 | 81 / 5 / 13 | **74 / 4 / 13** | 67 / 3 / 12 | 73 / 3 / 11 |
| Best AI's techs at turn 50 | 15 | 14 | **15** | 21 | 26 |
| Turn 100: score / cities / science / techs | 187 / 5 / 98 / 31 | 239 / 7 / 133 / 31 | **238 / 8 / 101 / 31** | 162 / 4 / 51 / 28 | 153 / 4 / 45 / 30 |
| Tech lead over the best AI at turns 100 / 150 | -1 / +13 | +3 / +15 | **-4 / +9** | -13 / -18 | -19 / (game over) |
| Cities lost | none | none | **none** | 1 | 3 |
| Final score and rank | 417, 2nd of 8 | 471, 1st of 8 | **442, 1st of 8** | 283, 8th of 8 | 191, 8th of 8 |
| Cost (per turn) | $91.67 ($0.539) | $79.27 ($0.472) | **$71.03 ($0.418)** | $65.14 ($0.374) | $51.00 ($0.386) |
| Wall clock (median per turn) | 6.5 h (104 s) | 5.7 h (105 s) | **5.3 h (88 s)** | 4.7 h (78 s) | 3.5 h (68 s) |

On King, Fable 5.2 played its Prince game: its techs at turns 50 and 100 match games 12 and 14 (13 and 31), its science led from turn 71, and the win came on turn 170, between games 14 and 12. What changed from King to Emperor was the start and the neighbors. On Emperor the AI civs had 21 techs by turn 50 to its 12, it had 3 cities instead of 4, and Spain took its capital on turn 86; it never closed the gap. On King nobody attacked it, and its 8 cities by turn 72 left it free to build. One game per level is a small sample, and the Emperor loss may owe as much to Spain's war as to the level, but on this map Fable 5.2 wins up to King and loses from Emperor on.

## The harness in this game

From the server log and the agent's tool results:

- **No AI-turn hangs.**
- **One reply lost on the connection.** On turn 131 the agent sent 11 orders in one `issue_orders` call. All 11 ran within 19 s, and the server began its reply (the HTTP log shows `200 OK`), but Claude Code never got it. 68 s later Claude Code reported "connection closed before the tool call was answered. The tool may have run", and opened a new session. The agent tried to send the same 11 orders again, but they never reached the server while Claude Code reconnected. Instead the agent read the overview, units, cities and notifications, and went on with new orders, so nothing ran twice. It is the only error in 1,176 calls, and the server log does not say why the reply was lost.
- **One end turn refused over a unit, reported in 70 s** (turn 65), the 45 s check's second use after game 16's.
- **The end-turn leader-screen check closed a screen for the first time.** On turn 90 a leader screen came up while `end_turn` waited for the AI turns; the check closed it and the turn ended 104 s after it was sent. Games 14 to 16 never needed it.
- **Trades**: the agent tested one trade (turn 63, no answer) and proposed one (Citrus to Brazil for 4 gold per turn on turn 146, accepted). It answered 19 AI offers: 13 accepted, among them alliances with Germany, Greece, Egypt and Brazil, and 6 refused.
- **Leader screens**: the harness closed a leader screen left open after a diplomacy answer 18 times, and left one alone 42 times because a diplomacy session was still open.
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 48 pauses; 28 times the game had already moved to the next turn, and 1 of those turns ended with no unit order.
- **Moves** said "arrived with no moves left" 110 times. **Move-and-attack** left 2 `STOPPED_SHORT`. **Auto-explore** was sent again 16 times, and `skip_remaining_units` left units with orders of their own alone in all 101 of its calls.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 170 is the agent's closing summary after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 170 (game window on top, war room below).
