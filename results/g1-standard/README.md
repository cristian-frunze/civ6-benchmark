# Game 1: Opus 5.5 vs the built-in AI, with the playbook

**Result: Science victory on turn 262.** Opus 5.5 (high effort) played Sumeria (Gilgamesh) against 7 built-in AI civs on Prince, on a standard Pangaea map at Quick speed, base game. It finished the last space project 68 turns before the 330-turn limit. By the agent's last diary entry, Greece had 3 of 5 projects done.

| | |
|---|---|
| Played | 2026-11-06, 5.6 hours wall clock |
| Turns | 262 (median 47 s per turn) |
| API-equivalent cost | **$67.83** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 368K output, 248M cache read, 1.36M cache write, 2.6K uncached input |
| API requests | 1,300 (about 5 per turn) |
| Tool calls | 1,951, of which 5 returned errors |
| Claude Code sessions | 4, all one conversation (3 restarts to deploy harness fixes, no usage limits hit) |

Cache reads are most of the bill ($49.54): every request rereads the whole conversation. Output was $7.36 and cache writes $10.92.

## Final standings (turn 262)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| Rome | 481 | 12 | 132 | 50 | 36 | 389 |
| **Sumeria (Opus 5.5)** | 476 | 9 | **262** | **66** | 36 | 794 |
| Greece | 450 | 11 | 158 | 59 | 38 | 194 |
| Egypt | 423 | 11 | 164 | 50 | 43 | 297 |
| America | 411 | 10 | 90 | 42 | 39 | 529 |
| Spain | 396 | 7 | 160 | 47 | 39 | 399 |
| Brazil | 359 | 6 | 50 | 37 | 42 | 311 |
| Germany | 318 | 8 | 62 | 39 | 30 | 1011 |

Rome finished just ahead on score. Opus won on science: 66 techs against 59 for the next civ, and 262 science per turn against 164.

## Cost and pace over the game

| Turns | API-equivalent $ | Median seconds per turn | Requests per turn |
|---|---|---|---|
| 1-50 | 8.03 | 39 | 5.1 |
| 51-100 | 14.24 | 46 | 5.0 |
| 101-150 | 16.34 | 62 | 6.0 |
| 151-200 | 15.07 | 54 | 5.3 |
| 201-262 | 14.15 | 40 | 3.7 |

## Harness incidents and interventions

This was the third start: the first two were thrown out at turns 1 and 3 (a stray click during the save load moved the settler, then a tutorial popup held the turn). See [docs/setup.md](../../docs/setup.md).

During this run the harness stalled three times, and each stall was fixed in `windows/civ_mcp_http.py`:

- Turns 10 and 13: `end_turn` waited about 10 minutes on a unit that still needed orders.
- Turn 92: a leader screen left open after an AI greeting held the AI turns. civ6-mcp reloaded turn 92 once, so the agent played that turn twice. After the fix, the server closed such a screen 12 more times in this game, and no later `end_turn` took longer than 95 s.

Everything done to the game from outside the agent is in [interventions.jsonl](interventions.jsonl). Each entry is a read-only harness call, a screen closed, or a restart to deploy a fix. None changed the game state.

The per-turn archive is missing screenshots for turns 2, 4-6, 8 and 144, and autosaves for turns 144 and 153.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and every city.
- [`shots/`](shots/): the screens at the start of turns 50, 130, 200 and the end (game window on top, war room below).
- [`interventions.jsonl`](interventions.jsonl): every action on the running game from outside the agent.

The agent's full transcripts (thinking summaries, messages, tool calls and results) and every autosave are kept for the public data export.
