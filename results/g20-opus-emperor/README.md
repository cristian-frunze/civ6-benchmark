# Game 20: Opus 5.5 on Emperor, goal: Science victory, Online speed

**Result: Defeat on turn 186. America (AI) won a Science victory.** Game 20 puts Opus 5.5 (high effort) on Emperor, the level where Fable 5.2 lost games 16 and 18, one above King, where Opus won game 19 (turn 218). Everything else is the same: Sumeria (Gilgamesh) against the same 7 built-in AI civs on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. Opus was last of 8 in score at turns 50, 100, 150 and the end, with half the leading AI's techs at turn 50 (11 to 22) and 17 fewer at the end; it never finished a space project. America finished its fifth as turn 186 ended, with Greece at 4. The harness is game 19's plus three fixes: a dropped end-turn request is sent again, `unit_action` has `pillage`, and spy messages are corrected.

| | |
|---|---|
| Played | 2026-11-12 17:31 to 22:02 CET, 4.5 hours wall clock, with no stalled end turns |
| Turns | 186 (median 63 s per turn) |
| API-equivalent cost | **$47.67** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 276K output, 171M cache read, 1.00M cache write, 1.9K uncached input |
| API requests | 937 (about 5.0 per turn) |
| Tool calls | 1,338, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context twice |

Cache reads are 72% of the bill ($34.12), cache writes 17% ($8.02) and output 12% ($5.52). By 50-turn range the game cost $7.20, $15.25, $14.82 and $10.40 (turns 151 to 186, plus the closing summary).

## Final standings (turn 186)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Greece | **597** | 10 | **445** | **68** | **51** | 1,049 | 4 |
| Germany | 582 | 10 | 259 | 63 | 39 | 965 | 0 |
| Egypt | 573 | **13** | 151 | 52 | **51** | **1,348** | 0 |
| Spain | 543 | 11 | 240 | 62 | **51** | 709 | 2 |
| **America (winner)** | 493 | 11 | 384 | 67 | 41 | 1,070 | **4, then 5** |
| Rome | 460 | 10 | 199 | **68** | 44 | 442 | 2 |
| Brazil | 372 | 5 | 155 | 60 | 35 | 371 | 0 |
| **Sumeria (Opus 5.5)** | **350** | **9** | **156** | **51** | **31** | **411** | **0** |

## How it went

Brazil and Spain declared war on turn 29, when Opus had 3 cities. It built walls and archers, neither attacked, and it made peace with both on turn 39. At turn 50 it had 4 cities and 11 techs to the best AI's 22, and the lowest score (66). On turn 57 it declared a surprise war on Brazil to take Salvador, which had no unit inside. Every attack on the city, melee and ranged, came back "No hostile unit", and moving onto it was blocked: civ6-mcp could not attack a city (below). The agent pillaged a coffee plantation instead, with the new pillage order, and made peace on turn 67. It then settled and built: 6 cities at turn 100 (28 techs to the best AI's 45) and 9 by turn 141 (Ur, Isin and Larak from turn 126). Its science was 7th of 8 at turns 100 and 150 (69 and 108 per turn). Germany became a friend and then an ally; the alliance lapsed on turn 155 and was renewed by turn 166. Spain, Brazil, Rome, Egypt and America denounced it, Egypt twice for its weak military. Spain declared war on turn 136 and took Kish, a size-9 city, on turn 146, the turn the agent had planned to offer peace; peace followed. A war with Greece from turn 172 to about 180 cost no city, and Sippar, settled on turn 180, brought it back to 9 cities.

America started the space race on turn 148 and had 3 projects by turn 160 and 4 by turn 181; Greece, Rome and Spain followed. Opus never finished a Spaceport: Lagash's would have been done about turn 192. From turn 181 it bought two spies to set back America's rocketry at Washington, and both were killed by turn 186, the turn America won. Its science was 6th of 8 at the end (156 per turn, to America's 384 and Greece's 445). The agent's last plan: "Two civs at 4 of 5 space projects, so the game may end soon. Keep maximizing score."

## Emperor: Fable 5.2 twice, Opus 5.5 once

| | Game 16 (Fable 5.2) | Game 18 (Fable 5.2) | **Game 20 (Opus 5.5)** | Game 19 (Opus 5.5, King, for reference) |
|---|---|---|---|---|
| Result | Defeat, turn 174 (Greece) | Defeat, turn 176 (Greece) | **Defeat, turn 186 (America)** | Science victory, turn 218 |
| Turn 50: score / cities / techs (best AI) | 67 / 3 / 12 (21) | 81 / 4 / 12 (25) | **66 / 4 / 11 (22)** | 64 / 3 / 12 (15) |
| Turn 100: score / cities / science / techs (best AI) | 162 / 4 / 51 / 28 (41) | 194 / 7 / 87 / 29 (44) | **182 / 6 / 69 / 28 (45)** | 206 / 9 / 82 / 27 (35) |
| Turn 150: score / cities / science / techs (best AI) | 247 / 6 / 164 / 41 (59) | 283 / 7 / 203 / 45 (63) | **270 / 8 / 108 / 42 (65)** | 325 / 9 / 264 / 45 (45) |
| Tech lead at the end | -16 | -10 | **-17** | 0 |
| Science rank at the end | 2nd | 1st | **6th** | 2nd |
| Its space projects at the end | 0 | 2 | **0** | 5 |
| Wars against it | Spain (turns 82 to 91), Egypt and Rome (121 to 133) | Rome (109 to 119) | **Brazil and Spain (29 to 39), Spain (136 to 146), Greece (172 to about 180); its own on Brazil (57 to 67)** | none (its own on Spain, 209 to 217) |
| Cities lost | Uruk, the capital (turn 86) | none | **Kish (turn 146)** | none |
| Final score and rank | 283, 8th of 8 | 336, 8th of 8 | **350, 8th of 8** | 470, 5th of 8 |
| Cost (per turn) | $65.14 ($0.374) | $75.31 ($0.428) | **$47.67 ($0.255)** | $64.28 ($0.295) |
| Wall clock (median per turn) | 4.7 h (78 s) | 4.9 h (80 s) | **4.5 h (63 s)** | 6.4 h (68 s) |

Opus on Emperor started like Fable 5.2 did: by turn 50 the leading AI had twice its techs (22 to 11), where on King it was 15 to 12. Fable 5.2 then out-researched every AI civ by the end of both its Emperor games (2nd and 1st in science); Opus never did, and its science stayed 6th or 7th of 8, so the gap ended at 17 techs, the widest of the three. It lasted longer than Fable 5.2 (turn 186 to 174 and 176) because the winning civ was slower, America here and Greece there, not because it was closer: it had no space project. It was also the cheapest of the three, at $0.255 a turn. With game 19, Opus 5.5 has now won up to King and lost on Emperor and Deity (game 5), the same line as Fable 5.2. Game 21 repeats this game.

## The harness in this game

From the server log and the agent's tool results:

- **No stalled end turns.** No end-turn request was dropped, so the resend added after game 19 never fired, and there were no AI-turn hangs.
- **No way to attack a city.** In the war on Brazil (turns 57 to 67), every attack on Salvador, which had no unit inside, returned `NO_ENEMY|No hostile unit`, and moving onto the city was blocked. civ6-mcp's attack looked only for units on the target tile, so a city with its own defenses but no garrison could not be hit. The agent noted "BUG: attack on enemy city with no garrison gives NO_ENEMY (both melee and ranged)" and made peace. From game 21, an attack on an enemy city centre or Encampment with no unit in it targets the district itself, reports its hit points before and after, and says when the city has been taken; an attack on any other district, which has no defenses, says so and points to pillage. Tested on this game's turn-58 save, a War-Cart took Salvador from 200 hit points to 156, and on turn 59 an archer and three War-Carts took the city.
- **Trade routes refused with no reason.** After Kish fell (turn 146), the trader whose last route had started there was refused for every destination with no reason, and on turn 169 another trader was refused in Bad-Tibira though route slots were free. The game's own trade screen makes the same check. From game 21, a refused route gives the game's reasons, the trader's city, and a note when the city its last route started from has been lost.
- **End turns refused over a unit: 8, each reported after about 70 s.** From game 21 the refusal comes back as soon as the game reports it, in about 30 s in tests.
- **Pillage** was used for the first time (turn 58, a coffee plantation); the agent noted it costs 3 moves.
- **Smaller problems the agent noted, not fixed yet**: a city's list of units it can attack included units of civs at peace (turns 77 and 172); the envoy blocker needed two `send_envoy` calls (turns 152 and 173); the settle advisor listed a tile Spain owned (turn 182).
- **Leader screens**: the harness closed a leader screen left open after a diplomacy answer 7 times, and left one alone 47 times because a diplomacy session was still open.
- **Auto-explore** was sent again 29 times, and `skip_remaining_units` left units with orders of their own alone in all 143 of its calls.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 187 is the agent's closing summary after the defeat screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 186 (game window on top, war room below).
