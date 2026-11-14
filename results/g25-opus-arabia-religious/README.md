# Game 25: Opus 5.5 as Arabia on Prince, goal: Religious victory, Online speed

**Result: Religious victory on turn 159, 2nd of 8 in score.** Game 25 is the second of three Opus 5.5 games (high effort) with other civs and other victory goals. Opus played Arabia (Saladin), a civ built for religion: it always gets the last Great Prophet, and its Madrasa adds faith. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the earlier games, in the base game with the playbook, but another leader changes the start and the AI civs: Arabia met Russia, India, China, Greece, America, England and Sumeria. The harness is game 24's, with its war-declaration and research fixes added only from game 26. Islam was the majority religion in all 8 civs when turn 159 ended, the first Religious victory in this benchmark, and the cheapest win of the Opus games so far: $50.03.

| | |
|---|---|
| Played | 2026-11-13 19:44 to 2026-11-14 00:44 CET, 5.0 hours wall clock |
| Turns | 159 (median 95 s per turn) |
| API-equivalent cost | **$50.03** at list prices, $0.31 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 365K output, 164M cache read, 1.24M cache write, 1.8K uncached input |
| API requests | 906 (about 5.7 per turn) |
| Tool calls | 1,390, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 3 times (turns 79, 122 and 145) |

Cache reads are 66% of the bill ($32.81), cache writes 20% ($9.91) and output 15% ($7.31). Turns 1 to 50 cost $7.54 (median 51 s a turn), 51 to 100 $15.57 (83 s), 101 to 150 $23.05 (140 s), and 151 to the end $3.87 (149 s). A religious game needs fewer orders than a war: about 5.7 requests a turn to game 24's 9.4.

## How it went

On turn 1 Opus wrote the plan it then followed: "Goal religious victory. Plan: Astrology -> Holy Site early, pantheon, expand to 5-6 cities." The early game was rough: barbarians took a scout, warriors, an archer and a trader. Russia founded Orthodoxy on turn 30, and Arabia missed the first Great Prophet on turn 36, but its guaranteed last one came on turn 43, and Opus founded Islam in Cairo with Feed the World and Pilgrimage. It took Classical Republic on turn 48 and Theocracy on turn 89. Hagia Sophia, finished on turn 99, gave every religious unit an extra spread.

From there the game was faith turned into Apostles and Missionaries: Opus bought 39 Apostles and 13 Missionaries and sent them to every civ it could reach, buying open borders where it had to (India and China on turn 128) and allying with America (turn 115) and Sumeria (125). The number of cities following Islam, out of all cities on the map:

| Turn | Islam | Hinduism (India) | Orthodoxy (Russia) | All cities | Civs with an Islam majority |
|---|---|---|---|---|---|
| 50 | 2 | 3 | 6 | 21 | |
| 75 | 8 | 9 | 7 | 34 | |
| 100 | 17 | 15 | 4 | 43 | 2 (turn 97) |
| 110 | 27 | 18 | 2 | 49 | 4 |
| 128 | 32 | 23 | 1 | 54 | 3: Greece lost to Indian apostles |
| 137 | 43 | 19 | 0 | 60 | 5 |
| 148 | 52 | 16 | 0 | 64 | 7 of 8 |
| 159 | 57 | 17 | 0 | 67 | 8 of 8 |

India was the rival. Its apostles spread Hinduism into Greece and back into its own cities, and they killed several of Opus's apostles in theological combat; Opus could not fight back (below). England was the last civ: its home cities lay across a strait, and Victoria refused open borders. England declared war on turn 152, which let Opus's apostles into English land. London flipped on turn 154, and Plymouth, the last English city, was found on turn 158 and tied 3:3 on turn 159. India held at 5 of its 9 cities, and the game ended on a Religious victory as turn 159 ended. In its closing summary Opus counted the war's cost: English units killed four apostles, two missionaries, a warrior and a trader.

Arabia was 5th in score at turn 50 (77 points, 5 cities), 2nd at turn 100 (220 to Russia's 223, 9 cities) and 2nd at the end. Opus spent its faith on religion and its production on districts and wonders, not an army: its military was 598 at the end, game 24's Scythia 3,357.

## Final standings (turn 159)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| Russia | 416 | 10 | 64 | 35 | 36 | 656 |
| **Arabia (Opus 5.5, winner)** | **376** | **12** | **147** | **43** | **30** | **598** |
| India | 365 | 9 | 110 | 41 | 31 | 576 |
| China | 311 | 8 | 52 | 35 | 34 | 466 |
| Greece | 299 | 8 | 148 | 43 | 25 | 216 |
| America | 294 | 7 | 92 | 38 | 31 | 591 |
| England | 259 | 6 | 68 | 36 | 23 | 372 |
| Sumeria | 230 | 7 | 73 | 36 | 21 | 164 |

## The harness in this game

From the run log and the agent's tool results:

- **No theological combat.** Twice, on turns 91 and 127, Opus attacked another civ's religious unit with an Apostle and got `Error: NO_ENEMY|No hostile unit or city at (x,y)`: civ6-mcp's attack found no foreign unit on the tile. Had it found one, it would still have refused, since it attacks only units of civs you are at war with, and theological combat needs no war. Opus concluded the tool could not do it and spread instead, while India's apostles kept attacking its own. Fixed after game 26: an attack by a religious unit now starts theological combat the way the game's own UI does, and on this game's turn-127 save an Apostle killed an Indian Apostle with it.
- **An unavailable tech was accepted.** On turn 115 `set_research` answered `RESEARCHING|TECH_ECONOMICS`, but Economics needs Scientific Theory, which Arabia did not have. The game asked for a tech again the next turn, and Opus reset to Astronomy ("Economics was not actually available"). From game 26, `set_research` and `set_civic` check that the item can be researched and answer `Error: NOT_AVAILABLE|... it needs <prerequisite> first`.
- **One AI-turn hang**, after Opus ended turn 147: a Russian diplomacy screen was up and India still held a deal it had not answered (a trade test earlier that turn got no answer within 6 s). `end_turn` reloaded the autosave from the start of turn 147 and ended the turn again, as designed; Opus re-entered that turn's orders. No other stalls, no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 160 is the agent's closing summary after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city, religion followers included.
- [`shots/`](shots/): the screens at the start of turns 50, 100 and 159 (game window on top, war room below).
