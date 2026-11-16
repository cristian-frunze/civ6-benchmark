# Game 33: Opus 5.5 as India on Prince, goal: Religious victory

**Result: Religious victory on turn 241, 1st of 8 in score (586 to Egypt's 573).** Opus 5.5 (high effort) played India (Gandhi) against seven AI civs: Russia, Greece, Brazil, Germany, America, Egypt and Sumeria. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the earlier games, and the leader changes the start and the rivals. It is the fourth Religious game: Arabia won game 25 on turn 159, and Russia lost games 29 and 31. The harness had the fixes from games 31 and 32: the Evangelize Belief order named in `unit_action`'s list, open borders bought in a deal given the game's duration, friendships and embassies checked against the game's state, and blocked moves explained from the game's facts.

| | |
|---|---|
| Played | 2026-11-16 00:03 to 09:01 CET, 9.0 hours wall clock (the run waited 2 h 45 min before that for a free Claude session slot on the machine that runs the agents) |
| Turns | 241 (median 112 s per turn) |
| API-equivalent cost | **$95.39** at list prices, $0.40 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 701K output, 317M cache read, 2.24M cache write, 3.3K uncached input |
| API requests | 1,644 (about 6.8 per turn) |
| Tool calls | 2,264, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions. It compacted its context 6 times (turns 86, 125, 159, 188, 210 and 230) |

Cache reads are 66% of the bill ($63.43), cache writes 19% ($17.93) and output 15% ($14.02). Turns 1 to 50 cost $8.10 (median 51 s a turn), 51 to 100 $16.37 (83 s), 101 to 150 $18.04 (112 s), 151 to 200 $29.82 (175 s), and 201 to the end $23.05 (196 s). The last 90 turns cost the most: dozens of Apostles and Missionaries moved and spread every turn.

## How it went

Opus's turn-1 plan: "India (Gandhi) - religious civ. Goal religious victory. Plan: Astrology -> Holy Site early to secure Great Prophet; pantheon ASAP." It took Divine Spark as its pantheon on turn 20 and founded Hinduism on turn 33 (Feed the World and Pilgrimage), after two AI civs had already founded religions. India's start was isolated: it met no other civ until about turn 75, with 5 cities, all Hindu.

Converting the rest of the map was slow. At turn 110 Hinduism was the majority in India and Brazil, 2 of the 6 civs met, while Egypt's Sikhism was in 24 cities. Opus switched to Theocracy (turn 87), bought religious units with faith (63 Apostles, 16 Missionaries and a Guru over the game) and used the Evangelize Belief order once, on turn 120, to add Mosque as a third belief. Games 29 and 31 never found that order. From turn 143 its Apostles fought: 13 theological attacks, 6 kills, mostly Inquisitors.

On turn 150 Opus changed course: "Religious victory stalling (2/6) ... limited war on Brazil to capture Rio (Catholic holy city) + Curitiba/Brasília; this helps both religion (removes Catholic pressure, reduces Brazil city count) and score." It declared a surprise war on turn 155 and took Salvador (turn 162), Brasília (167), Curitiba (170) and Rio de Janeiro (179). Brazil then paid for peace on turn 179: a Great Work, 121 gold and 37 gold a turn for 30 turns. With Brazil down to 5 cities, Hinduism held the majority in 5 of 8 civs by turn 190.

Sumeria had 2 of 5 space projects by turn 190. Opus used a spy against it, then declared a formal war on turn 202 and pillaged Sumerian Campuses (34 pillages over the game), which also sped up India's own research. Sumeria made peace on turn 239, giving Iron and 6 gold.

Egypt held out longest: Hinduism was in 1 of its 12 cities at turn 230, 3 at turn 235 and 5 at turn 240, with Egyptian Inquisitors removing it again and again ("they reset Memphis to zero once", in Opus's closing summary). On turn 241 Thebes and Swenett flipped and one more spread at Memphis, tied 5 to 5, made 7 of 12. Hinduism was the majority in all 8 civs, and India won.

| Turn | Score (rank) | Cities | Cities following Hinduism | Faith / turn | Civs with a Hindu majority | Military (best AI) |
|---|---|---|---|---|---|---|
| 50 | 93 (2nd) | 5 | 6 | 11 | India (no other civ met) | 120 (215) |
| 100 | 226 (2nd) | 8 | 12 | 93 | 2 of 6 met (turn 110) | 365 (406) |
| 150 | 336 (2nd) | 11 | 24 | 190 | 2 of 6 | 399 (679) |
| 200 | 522 (1st) | 15 | 38 | 321 | 5 of 8 (turn 190) | 1,078 (1,233) |
| 241 | 586 (1st) | 15 | 62 | 350 | 8 of 8 | 1,702 (1,512) |

## Final standings (turn 241)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| **India (Opus 5.5, winner)** | **586** | **15** | **175** | **63** | **45** | **1,702** |
| Egypt | 573 | 12 | 110 | 48 | 51 | 795 |
| Germany | 562 | 11 | 171 | 54 | 51 | 1,512 |
| Greece | 544 | 11 | 234 | 68 | 51 | 0 |
| America | 514 | 12 | 121 | 49 | 51 | 343 |
| Sumeria | 422 | 12 | 158 | 65 | 41 | 187 |
| Brazil | 346 | 5 | 37 | 46 | 37 | 184 |
| Russia | 327 | 8 | 105 | 42 | 28 | 244 |

## Four Religious games

| Game | Civ | Result | Religious units bought | Theological attacks (kills) | Cost | Hours |
|---|---|---|---|---|---|---|
| 25 | Arabia | Religious victory, turn 159 | 39 Apostles, 13 Missionaries | 0 (the harness had no theological combat yet) | $50.03 | 5.0 |
| 29 | Russia | Defeat (Egypt, Culture), turn 224; Orthodoxy majority in 6 of 8 | 56 Apostles, 9 Missionaries | 0 | $90.88 | 9.0 |
| 31 | Russia, fixed harness | Defeat (Greece, Science), turn 223; majority in 4 of 8 | 54 Apostles, 2 Missionaries | 17 (6) | $84.74 | 6.9 |
| 33 | India | Religious victory, turn 241 | 63 Apostles, 16 Missionaries, 1 Guru | 13 (6) | $95.39 | 9.0 |

India's start and rivals differ from Arabia's and Russia's, so the four games compare loosely. Game 33 is the one where the agent also went to war for the religion, taking Brazil's holy city.

## The harness in this game

From the run log and the agent's tool results:

- **The Evangelize Belief order was found and used** (turn 120), now that `unit_action`'s list of actions names it. Mosque became Hinduism's third belief.
- **Friendships were checked.** Three declarations to Sumeria came back confirmed by the game's state ("the game now shows a declared friendship").
- **Four delegations and one embassy came back `NOT_ACCEPTED`** (Sumeria turn 75, Brazil 83, Egypt 93, Russia 99; America's embassy 176). `get_diplomacy` still offered a delegation to those civs afterwards, so none took effect; before game 33 civ6-mcp would have called each one accepted. Replayed after game 34 on this game's turn-75 save, Sumeria answered the delegation with the game's refusal statement (`AI_REFUSE_DEAL`) and no gold changed hands: the AI civs did decline.
- **The new note on moves that stopped short was sometimes wrong.** About 1,250 moves stopped before their target. In 260 of them the harness replaced civ6-mcp's "moves exhausted" with the moves the game showed left, and in 13 it showed 4 or 5, a full Apostle or Missionary allowance or more, after the unit had moved 1 to 7 tiles. Opus noticed on turn 241: "the reported '4 moves left' looks stale". The note read the moves from the game's UI state, which can lag behind the move. Fixed after game 34: the moves and zone of control now come from the game core, where civ6-mcp reads the unit's new position. Replayed on this game's turn-241 save, the same Missionary order (from (57,37), 4 moves) now ends "moves exhausted", and both states show 0 moves a moment later.
- **One AI-turn hang** (turn 94): the harness reloaded the turn's save and ended it again, and Opus replayed the turn, knowing that Brazil would demand it stop proselytizing. It refused again.
- No tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 242 is the agent's closing summary after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150, 200 and 241 (game window on top, war room below).
