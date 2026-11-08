# Game 5: Opus 5.5 vs the built-in AI on Deity, goal: Science victory, Online speed

**Result: Defeat on turn 144. Greece (AI) won a Science victory.** Opus 5.5 (high effort) played Sumeria (Gilgamesh) against the same 7 built-in AI civs as game 3, on the same standard Pangaea map and start (same seed), Online speed, 250-turn limit, base game, playbook, Science goal. The only change from game 3 is the difficulty: Deity, the hardest level, instead of Prince. On Deity the AI civs start with extra settlers and units and get large yield bonuses all game. Greece finished its fifth space project during the AI turn after turn 144, and Opus finished last on every measure.

| | |
|---|---|
| Played | 2026-11-08 09:41 to 13:42 CET, 4.0 hours wall clock |
| Turns | 144 (median 60 s per turn) |
| API-equivalent cost | **$37.80** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 239K output, 131M cache read, 860K cache write, 1.5K uncached input |
| API requests | 755 (about 5.2 per turn) |
| Tool calls | 1,133, of which 1 returned an error |
| Claude Code sessions | 1: the whole game in one conversation, with no usage limits or interventions |

## Final standings (turn 144)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| Germany | 549 | 13 | 146 | 49 | 49 | 1,066 | 0 |
| Egypt | 522 | 10 | 278 | 66 | 51 | 986 | 2 |
| America | 504 | 10 | 254 | 63 | 37 | 1,419 | 1 |
| Spain | 497 | 9 | 361 | 68 | 51 | 2,304 | 2 |
| Brazil | 491 | 11 | 141 | 49 | 46 | 521 | 0 |
| **Greece (winner)** | 454 | 9 | 346 | 68 | 44 | 1,035 | **4, then 5** |
| Rome | 415 | 11 | 362 | 61 | 46 | 790 | 0 |
| **Sumeria (Opus 5.5)** | **218** | **5** | **97** | **37** | **22** | **221** | 0 |

## How it went

Opus was behind from the first turns and never caught up. On turn 50 it had 4 cities and 11 techs; the AI civs had 5 or 6 cities and 21 to 23 techs. Barbarians besieged its cities from turn 39 to about turn 55 and held up its expansion. By turn 100 Greece already had a space project and Opus wrote: "Science victory not realistic; playing to survive and maximize score/science."

- **Turn 98:** Rome and Germany declared war, with Rome's army around Uruk, the capital. Spain joined soon after.
- **Turn 99:** the agent reloaded the turn's autosave itself after a unit move went wrong.
- **Turn 104:** Spain took Lagash (population 8, with a University). Uruk held, and by turn 106 Opus had destroyed most of Rome's siege army around it.
- **Turns 130-144:** Greece sat at 4 of 5 space projects from turn 136 and finished the fifth after turn 144.

Opus's own game was only somewhat weaker than on Prince. The AI's was far stronger:

| | Game 3 (Prince) | Game 5 (Deity) |
|---|---|---|
| Opus at turn 50: score / techs | 83 / 11 | 72 / 11 |
| Opus at turn 100: score / cities / techs | 185 / 6 / 27 | 174 / 6 / 28 |
| Opus at turn 144: score / cities / techs | 278 / 6 / 42 | 218 / 5 / 37 |
| Best AI at turn 100: score / techs | 231 / 31 | 385 / 45 |
| Best AI at turn 144: score / techs | 334 / 39 | 549 / 68 |
| Average AI score at turn 144 | 295 | 490 |
| Result | Science victory, turn 212 | Greece's Science victory, turn 144 |
| Cost | $56.43 | $37.80 (a shorter game) |

On Prince, Opus at turn 144 trailed the best AI's score but led it in techs (42 to 39). On Deity, every AI civ had more techs than Opus by turn 50, and the gap grew to 31 techs by the end.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50 and 130 and at the end (game window on top, war room below).
