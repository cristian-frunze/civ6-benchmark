# Hotseat game h2: one Opus 5.5 agent and seven built-in AI civs, Online speed

**Result: Science victory on turn 168 by Sumeria (Opus).** One Opus 5.5 agent (high effort) played Sumeria (Gilgamesh) in a hotseat game; the built-in AI played the other seven civs (Rome, Greece, Brazil, Germany, America, Egypt, Spain) on Prince. Map: standard Pangaea, same seed as games 3 and 4 and h1, Online speed, 250-turn limit, base game, playbook, no assigned goal. The agent was told it was the only agent in the game.

This is setup (A) of experiment 4, the control for h1: the same game with one agent instead of four.

| | |
|---|---|
| Played | 2026-11-08 06:41 to 09:37 CET, 2.9 hours wall clock |
| Turns | 168 (median 53 s per agent turn; a whole round took a median 60 s) |
| API-equivalent cost | **$78.02** at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 347K output, 246M cache read, 2.73M cache write, 2.9K uncached input |
| API requests | 1,720 (about 10.2 per turn) |
| Claude Code sessions | one, resumed once per turn |
| Interventions | none: no AI-turn hangs, retries or reloads |

Cache reads were $49.23, cache writes $21.85, output $6.93.

## Final standings (turn 168, the turn of the win)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| Germany | 485 | 10 | 116 | 45 | 36 | 859 |
| **Sumeria (Opus 5.5)** | **470** | 9 | **328** | **65** | 32 | 777 |
| Rome | 413 | 11 | 108 | 43 | 37 | 839 |
| America | 324 | 9 | 66 | 40 | 26 | 292 |
| Brazil | 318 | 6 | 103 | 40 | 27 | 495 |
| Egypt | 264 | 6 | 150 | 45 | 26 | 292 |
| Greece | 229 | 6 | 51 | 36 | 26 | 79 |
| Spain | 163 | 2 | 24 | 30 | 20 | 80 |

## How it went

Opus led on score from turn 63 to turn 158, when Germany took Greece's capital Sparta and passed it. By the end it had 65 techs to the best AI's 45 (+20) and more than twice the science per turn of any AI civ (328 to Egypt's 150).

- **Turns 31-46:** America and Spain declared war; both accepted peace by turn 46.
- **Turn 114:** Brazil declared war and sent knights at Shuruppak; Opus bought walls and held.
- **Turn 129:** first Spaceport, in Uruk.
- **Turn 132:** Rome and Germany declared war, with more than twice Opus's military. City walls held every city; Opus lost none.
- **Turns 138, 148, 156:** Earth Satellite, Moon Landing, Mars Habitation.
- **Turn 166:** bought Great Engineer Sergei Korolev for 1,850 gold. On turn 167 it tried to activate him on an Industrial Zone and learned that he only works on a Spaceport.
- **Turn 168:** activated Korolev on Uruk's Spaceport, which finished the Mars Reactor. Mars Hydroponics had finished in Bad-Tibira on turn 164: 5 of 5.

As in h1, the win came in the middle of the agent's turn and froze it (the agent reported that it could not end the turn). The runner's new check after every seat turn read the winner from the game and stopped cleanly.

## Compared with game 3 and h1

Game 3 is the closest single-player game: same map, seed, civ and opponents, Online speed, playbook. It differs in three ways: it is single player (civ6-mcp over FireTuner, one conversation for the whole game), its system prompt names a Science goal, and h2 uses the hotseat harness (the Johnor12 fork of civ6-mcp over the MCP Bridge mod, one session resumed each turn).

| | Game 3 (single player, Science goal) | h2 (hotseat, one agent, no goal) | h1 (hotseat, four agents) |
|---|---|---|---|
| Result | Science victory, turn 212 | Science victory, turn 168 | Science victory by Rome (an agent), turn 157 |
| Sumeria at turn 100: score / cities / science / techs | 185 / 6 / 66 / 27 | 268 / 8 / 191 / 36 | 262 / 9 / 196 / 34 |
| Sumeria at turn 150: score / techs | 293 / 44 | 436 / 59 | 384 / 57 |
| Cost | $56.43 | $78.02 | $277.02 (four seats) |
| Cost per turn | $0.27 | $0.46 | $0.44 per seat |
| Requests per turn | 5.2 | 10.2 | 9.1 per seat |
| Wall clock | 4.6 h | 2.9 h | 12.2 h |

The h2 agent played a much stronger game than game 3's on the same map: by turn 100 it had 45% more score, nearly three times the science and 9 more techs, and it won 44 turns earlier. It also spent about twice as many requests per turn. One game each can't say whether that comes from the harness, the missing goal, or ordinary variance between games. Game 7 repeats game 3 exactly to measure that variance.

Against h1: alone, Sumeria won; with three other agents in the game, Sumeria (Opus-A) came 5th and had 1 of 5 space projects when Rome won. h1 ended 11 turns earlier than h2, won by an agent playing Rome.

## Files

- [`game.json`](game.json): settings and the seat.
- [`turns.jsonl`](turns.jsonl): one row per agent turn with seconds, API requests, tokens, API-equivalent dollars, tries and the agent's closing message.
- [`rounds.jsonl`](rounds.jsonl): one row per round with every major civ's score, cities, yields, techs, civics and military, and the winning team (the last row has the win).
- `diary.jsonl.gz`: civ6-mcp's per-turn rows for every civ.
