# Game 23: Haiku 5.5 on Prince, goal: Science victory, Online speed (stopped on turn 83)

**Result: none. The run was stopped on turn 83 at the user's request**, to spend the game PC on Opus 5.5 games with other civs and victory types. Game 23 put Haiku 5.5 (high effort), the cheapest current model, in the Prince setup the other models won: Sumeria (Gilgamesh) against the same 7 built-in AI civs on the same standard Pangaea map and start (same seed, `BENCH_PANGAEA_ONLINE_T1`), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. The harness is game 22's plus the government checks and the no-going-back rule. The saves of turns 79 to 83 are kept on the game PC, so the game can be resumed.

| | |
|---|---|
| Played | 2026-11-13 09:21 to 10:44 CET, 1.4 hours wall clock |
| Turns | 83 (median 55 s per turn) |
| API-equivalent cost | **$2.43** at list prices, $0.029 a turn (Haiku 5.5: $0.10 / $0.50 per MTok in / out, $0.01 cache read, $0.20 cache write with the 1-hour TTL, for prompts up to 100K tokens; $0.50 / $2.50, $0.05 and $1 above) |
| Tokens | 266K output, 47.6M cache read, 0.62M cache write, 1K uncached input |
| API requests | 485, 228 of them over 100K tokens and priced on the long-prompt card |
| Tool calls | 566, 1 returned an error (the stop on turn 83) |
| Claude Code sessions | 1, with no compaction; one intervention, the stop |

Cache reads were 65% of the bill ($1.58), output 18% ($0.44) and cache writes 17% ($0.41).

## Where it stood

| Turn 50: score / cities / science / techs (best AI) | Turn 83: score / cities / science / techs (best AI) | Cost to turn 83 |
|---|---|---|
| **Game 23, Haiku 5.5:** 63 / 4 / 11 / 10 (15) | **111 / 6 / 21 / 17 (23), 7th of 8 in score** | **$2.43** |
| Game 13, Sonnet 5.5: 72 / 4 / 19 / 10 (17) | 131 / 6 / 44 / 18 (27) | $10.35 |
| Game 10, Opus 5.5: 77 / 4 / 22 / 14 (15) | 168 / 8 / 61 / 22 (26) | $20.06 |
| Game 12, Fable 5.2: 80 / 4 / 24 / 13 (15) | 154 / 5 / 66 / 26 (24) | $31.92 |

Haiku expanded at the pace of the others (4 cities at turn 50, 6 by turn 60) but built less science: 21 a turn at turn 83, half of Sonnet's and a third of Opus's at the same turn. Barbarians pressed it from turn 40 on, and on turn 83 a barbarian swordsman and men-at-arms were at Uruk and Kish. It also misread where it stood: from turn 60 its notes compared it with Spain only ("Sumeria leads with score 108 against Spain at 97", turn 80), the one civ behind it, while Egypt had 200 by turn 83. It played fast and cheap: 55 s and 3 cents a turn, mostly through `issue_orders` batches and end turns, with few map reads (5 `get_map_area` calls in 83 turns).

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests (and how many were long-prompt), tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`interventions.jsonl`](interventions.jsonl): the stop.
- [`shots/`](shots/): the screens at the start of turns 50 and 83.
