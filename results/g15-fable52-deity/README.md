# Game 15: Fable 5.2 on Deity, goal: Science victory, Online speed

**Result: Defeat on turn 132. Greece (AI) won a Science victory.** Game 15 is game 5's setup with Fable 5.2 (high effort) in place of Opus 5.5: Sumeria (Gilgamesh) against the same 7 built-in AI civs on Deity, the hardest level, on the same standard Pangaea map and start (same seed), at Online speed with the 250-turn limit, in the base game with the playbook and the Science goal. Fable 5.2 won both of its games on Prince (turns 168 and 170); on Deity it finished last, as Opus did in game 5, and Greece won 12 turns earlier than it did there. The harness is game 14's plus two fixes: an end turn the game refuses over a unit is reported at 45 s (a692ba5), and the trade test asks the AI's own check when its terms come back unchanged (0388838).

| | |
|---|---|
| Played | 2026-11-11 11:10 to 14:43 CET, 3.5 hours wall clock, with no AI-turn hangs |
| Turns | 132 (median 68 s per turn) |
| API-equivalent cost | **$51.00** at list prices (Fable 5.2: $8 / $40 per MTok in / out, $0.20 cache read, $16 cache write with the 1-hour TTL). At Fable 5.1's prices the same tokens would cost $63.75 |
| Tokens | 278K output, 141M cache read, 729K cache write, 1.4K uncached input |
| API requests | 689 (about 5.2 per turn) |
| Tool calls | 800, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 2 times |

Cache reads are 55% of the bill ($28.21), cache writes 23% ($11.66) and output 22% ($11.11).

## Final standings (turn 132)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Space projects |
|---|---|---|---|---|---|---|---|
| **Greece (winner)** | **514** | **12** | **312** | **68** | 47 | 1,248 | **3, then 5** |
| Spain | 449 | 7 | 296 | 65 | 49 | **1,334** | 3 |
| Rome | 442 | 11 | 275 | 67 | 42 | 323 | 2 |
| Germany | 429 | 11 | 216 | 49 | 37 | 803 | 0 |
| Egypt | 429 | 10 | 116 | 46 | 45 | 121 | 0 |
| Brazil | 401 | 9 | 118 | 45 | 48 | 656 | 0 |
| America | 394 | 9 | 106 | 43 | **50** | 696 | 0 |
| **Sumeria (Fable 5.2)** | **191** | **6** | **80** | **35** | **24** | **58** | 0 |

The space project counts are the last ones the game reported to the agent (turn 131). Greece finished its last two as turn 132 ended.

## How it went

Fable 5.2 was last in score from the first turns to the end. It had 3 cities until turn 56 and 6 by turn 69; at turn 50 it had 11 techs to the AI's 16 to 26. On turn 84 it sold Spain Horses for 11 gold per turn and Coffee for 130 gold. Spain declared war at the end of turn 87 with about 5 times its military, killed its War-Cart, and took Eridu on turn 91 and Uruk, the capital, on turn 96, when the agent made peace. Rome declared war at the end of turn 100 and took Sippar on turn 108; peace came the same turn. The agent founded Isin and Umma on turns 106 and 107 and Bad-Tibira on turn 131 to get back to 6 cities, and its science reached 80 per turn. By then Greece had 3 space projects (its first by turn 92, the third by turn 109), Spain 3 and Rome 2. In its last turns the agent wrote: "Science victory out of reach realistically; maximizing science/score and survival." Its summary after the defeat: "The game was effectively lost in the two Deity invasions."

## Compared with game 5 (Opus 5.5 on Deity)

| | Game 5 (Opus 5.5) | Game 15 (Fable 5.2) |
|---|---|---|
| Turn 50: score / cities / techs | 72 / 4 / 11 | 73 / 3 / 11 |
| Turn 100: score / cities / science / techs | 174 / 6 / 74 / 28 | 153 / 4 / 45 / 30 |
| Turn 132: score / cities / science / techs | 195 / 5 / 96 / 34 | 191 / 6 / 80 / 35 |
| Best AI at turn 100: score / techs | 385 / 45 | 341 / 49 |
| Best AI at turn 132: score / techs | 486 / 66 | 514 / 68 |
| Cities lost | Lagash (turn 104, to Spain) | Eridu and Uruk (turns 91 and 96, to Spain), Sippar (turn 108, to Rome) |
| Result | Greece's Science victory, turn 144 | Greece's Science victory, turn 132 |
| Final rank | 8th of 8 | 8th of 8 |
| Cost (per turn) | $37.80 ($0.263) | $51.00 ($0.386) |
| Wall clock (median per turn) | 4.0 h (60 s) | 3.5 h (68 s) |

On Deity the two models played about the same game. Both had 11 techs at turn 50 and about 35 at turn 132, both were invaded around turn 90 to 108, and both finished far behind every AI civ. Fable 5.2's lead on Prince (a tech lead of 15 at turn 150 there, 33 techs behind here) came from out-teching AI civs that research slowly; on Deity the AI civs get large yield bonuses, and neither model came close. Greece won 12 turns earlier here, but the AI civs' play varies from game to game, so one game cannot say whether Fable 5.2 made Greece's win come sooner.

## The harness in this game

From the server log and the agent's tool results:

- **No AI-turn hangs, no tool errors, and no end turns refused over a unit**, so the new 45 s check never had to name one. The end-turn leader-screen check never closed a screen either.
- **The trade test's new check was used, and its prices held.** Fable 5.2 ran 43 trade tests on turns 84, 87, 91, 95 and 121: 14 `ACCEPTABLE`, 23 `NOT ACCEPTABLE as-is`, 5 `REJECTED` and 1 with no answer. It used them to find each civ's price: Spain's Horses tested acceptable for 100, 150 and 175 gold and for 9 and 11 gold per turn, and not for 200 gold or 12 and 14 per turn. It then sent 5 proposals at or near those prices, and all 5 were accepted: Horses to Spain for 11 gold per turn and Coffee for 130 gold, Marble and Citrus to Greece for 111 gold and 2 gold per turn, and Truffles for 4 per turn, and Coffee to America for 125 gold. In game 14, before the check, 3 of 11 proposals were accepted.
- **Most of the AI offers it accepted were its own old terms.** The agent accepted 8 offers. 7 had the exact terms of a test or proposal it had made to that civ earlier: Coffee for 100 gold, which Egypt refused in a test on turn 95, came back as "Deal from Egypt" with an agenda complaint on turn 100, "you settle too close" on turn 106 and a denouncement on turn 114, and Greece's Horses for 3 gold per turn from a turn-91 test came back on turns 92, 112, 113 and 121. Only turn 92's went into effect. The other 6 never paid (by turn 99 the agent had no Coffee left to give), though `respond_to_trade` said `DEAL_UNCLEAR` on turn 100 and `DEAL_ACCEPTED` on the other five, as the AI turns were paused. civ6-mcp shows a civ's incoming working deal with every session it opens, and a closed trade session left that deal filled; replayed from the turn-95 autosave, the refused test left Coffee for 100 gold in both working deals with Egypt. From game 16 every trade call empties them ([setup](../../docs/setup.md)). Games 12 to 14 had 1 such offer between them (game 14, turn 115), and it went into effect.
- **Leader screens**: the harness closed a leader screen left open after a diplomacy answer 56 times.
- **Diplomacy-pause trap** (`tools/turn_trap.py`): 33 pauses; 25 times the game had already moved to the next turn, and 4 of those turns ended with no unit order.
- **Moves** said "arrived with no moves left" 53 times. **Auto-explore** was sent again 14 times, and `skip_remaining_units` left units with orders of their own alone 50 times.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 133 is the agent's summary after the defeat screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for the agent's cities.
- [`shots/`](shots/): the screens at the start of turns 50, 100 and 132 (game window on top, war room below).
