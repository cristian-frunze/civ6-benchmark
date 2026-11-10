# Game 11: game 9 repeated on the fixed harness (Fable 5.1, high effort), goal: Science victory, Online speed

**Result: Defeat on turn 209. Greece (AI) won a Science victory.** Greece (Gorgo) finished its fifth space project during the AI turns of turn 209. Fable 5.1 had four of its five projects done; its last, the Mars Reactor, was about 5 turns away. Game 11 is game 9 run again: Fable 5.1 at high effort playing Sumeria (Gilgamesh), against the same 7 built-in AI civs on Prince, on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. The one change is the harness: game 10's, plus the turn snapshot fix (730ef83). Game 9 won on turn 203, and game 10 (Opus 5.5 on this harness) on turn 200.

| | |
|---|---|
| Played | 2026-11-10 04:40 to 11:23 CET, 6.7 hours wall clock |
| Turns | 209 (median 94 s per turn) |
| API-equivalent cost | **$106.37** at list prices (Fable 5.1: $10 / $50 per MTok in / out, $0.25 cache read, $20 cache write with the 1-hour TTL) |
| Tokens | 602K output, 158M cache read, 1.82M cache write, 27K uncached input |
| API requests | 839 (about 4.0 per turn) |
| Tool calls | 1,483, of which 1 returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 5 times |

Cache reads are 37% of the bill ($39.58), cache writes 34% ($36.44) and output 28% ($30.08).

## Final standings (turn 209, before the AI turns)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Egypt | 660 | 15 | 178 | 50 | 51 | 890 | 0 |
| **Sumeria (Fable 5.1)** | **548** | 11 | **373** | **68** | 45 | 903 | **4** |
| Greece | 538 | 15 | 216 | **68** | 39 | 890 | 4, then 5 (won) |
| Rome | 466 | 11 | 175 | 65 | 37 | 265 | 1 |
| Brazil | 425 | 8 | 82 | 41 | 47 | 482 | 0 |
| America | 367 | 6 | 80 | 44 | 38 | 605 | 0 |
| Germany | 330 | 10 | 56 | 39 | 30 | 626 | 0 |
| Spain | 142 | 1 | 4 | 31 | 29 | 10 | 0 |

Spain lost four of its five cities between turns 177 and 199, while Egypt, Greece and Rome each gained cities.

## How the space race went

Greece finished its first space project on turn 150, its second on 156 and its third on 167, all before Sumeria's first. The agent saw it at once ("GREECE HAS 1/5 SPACE PROJECTS ... real science-victory threat", turn 150) and answered with spies. It lost three: one was killed at Sparta, and one was caught after a sabotage. It also tried the mission made for this, Disrupt Rocketry, against a Greek city on turn 172, and the harness answered `UNKNOWN_MISSION` (below). From then on its notes say Greece "can't be stopped militarily (25+ tiles away) nor via spy". Greece then stalled for 36 turns. Sumeria's projects came on turns 175, 191, 207 and 208, and the agent chopped forests into the Mars Reactor, cutting it from 20 turns to about 5. Greece's fourth project came on turn 203 and its fifth on 209. In its closing summary the agent blamed its late spaceports: Greece built Mars modules in four spaceports at once from about turn 190, while Sumeria's third and fourth spaceports came too late to matter.

## Compared with games 9 and 10

| | Game 9 (Fable 5.1, old harness) | Game 10 (Opus 5.5, this harness) | Game 11 (Fable 5.1, this harness) |
|---|---|---|---|
| Result | Science victory, turn 203 | Science victory, turn 200 | **Defeat, turn 209** (Greece's Science victory) |
| Turn 50: score / cities / techs | 66 / 4 / 9 | 77 / 4 / 14 | 80 / 4 / 12 |
| Turn 100: score / cities / science / techs | 197 / 6 / 71 / 28 | 233 / 8 / 137 / 31 | 196 / 7 / 78 / 31 |
| Turn 150: score / cities / science / techs | 321 / 7 / 233 / 48 | 346 / 8 / 226 / 48 | 350 / 11 / 180 / 45 |
| Turn 200: score / science / techs | 423 / 221 / 67 | 446 / 331 / 67 | **528** / 339 / 68 |
| Tech lead over the best AI at turns 100 / 150 / 200 | -3 / +8 / +18 | +1 / +7 / +6 | -4 / -5 / +2 |
| Space projects done (turn reached) | 1 (168), 2 (182), 3 (193), 4 (194), 5 (203) | 1 (161), 2 (179), 3 (184), 4 and 5 (200) | 1 (175), 2 (191), 3 (207), 4 (208) |
| Best AI's space projects | 1 | 2 (Greece) | 5 (Greece: 150, 156, 167, 203, 209) |
| Final score and rank | 428, 4th of 8 | 446, 2nd of 8 | 548, 2nd of 8 |
| Cost | $102.47 | $58.24 | $106.37 |
| Cost per turn | $0.505 | $0.291 | $0.509 |
| Requests per turn | 4.5 | 5.5 | 4.0 |
| Output tokens / thinking characters | 468K / 304K | 323K / 215K | 602K / 365K |
| Wall clock (median per turn) | 6.0 h of play (84 s) | 5.5 h (62 s) | 6.7 h (94 s) |

The same model, prompt and start played a different game. Game 9 stayed at 6 to 7 cities and built a science lead of 18 techs. Game 11 grew to 11 cities by turn 150 and had the best turn-200 score of any game so far (528; the eight others that reached turn 200 scored 350 to 446), but its tech lead was negative until turn 200 and its first space project came 7 turns later than game 9's. The bigger difference was Greece. In game 9 no AI finished more than one space project; in game 11 Greece had three by turn 167. The AI civs react to what the player does, so the same seed does not give the same opponents: games 3 and 7 (Opus, same setup) already finished 6 turns apart. One game per model is a small sample, and this game shows how far one run can swing.

## The fixes at work

From the server log and the agent's tool results:

- **No AI-turn hangs**, now with trade proposals. The agent proposed 26 trades (game 10: none) and answered 39 AI deals. In game 8, proposals caused most of its 18 hangs.
- **Turn reports kept their events.** The turn snapshot failed 0 times in 209 turns (game 10: 42 of 200 reports lost their events). The fix (730ef83) holds over a whole game.
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 64 pauses. The game had already moved to the next turn 33 times, and each time `end_turn` reported the new turn. None of those turns ended with no unit order.
- **Moves** said "arrived with no moves left" 134 times, and 1 `improve` order was refused for lack of moves. **Move-and-attack** results were read again 19 times after the order played out (1 `STOPPED_SHORT` left). **Auto-explore** was sent again 12 times, and `skip_remaining_units` left units with orders of their own alone 29 times. The harness closed a diplomacy screen left open 29 times.
- `NO_SESSION`, `SILENT_FAILURE` and `InvitePopup` never came up.

Found in this game:

- **Spies could not disrupt a spaceport.** civ6-mcp hardcodes its spy missions and leaves out two that the base game has: Disrupt Rocketry, which sets back a space project in a city with a Spaceport, and Listening Post. So `get_spies` never offered them, and the agent's `DISRUPT_ROCKETRY` on turn 172 came back `UNKNOWN_MISSION`. Whether a working mission would have changed the result is unknown: the agent's spies were being caught, and a success sets back only one city's project. Fixed in 5379f94 (see [setup](../../docs/setup.md)). Game 12 runs on this game's harness for a fair Fable 5.2 comparison, so the fix loads from game 13.
- On turn 190 the agent wrote that a spy's "Choose Escape Route" prompt could not be answered. civ6-mcp had answered it at the end of the turn ("Aban escaping via ..."), and the spy was caught anyway. That was a misreading, not a fault.
- `form_alliance` was sent 18 times to civs already allied (`ALREADY_ALLIED`; game 9: 10).

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. The last row (turn 210) is the agent's closing summary after the defeat.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 130, 200 and 209 (game window on top, war room below).
