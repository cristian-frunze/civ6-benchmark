# Game 26: Opus 5.5 as France on Prince, goal: Culture victory, Online speed

**Result: Defeat. Greece (AI) won a Science victory on turn 242, with Opus 2nd of 8 in score.** Game 26 is the third of three Opus 5.5 games (high effort) with other civs and other victory goals. Opus played France (Catherine de Medici), a civ built for culture: its wonders get extra production and its Chateau improvement gives culture. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the earlier games, in the base game with the playbook, but another leader changes the start and the AI civs: France met Russia, India, Brazil, Greece, America, Egypt and Sumeria. The harness is game 25's with the research and war-declaration fixes. Opus was 1st in score on 91 of the 93 turns from turn 150, built nine wonders and had the most culture per turn at the end, but no culture win in sight, and it had allied with the civ that won the space race. Three harness faults hid the culture race from it (below).

| | |
|---|---|
| Played | 2026-11-14 01:00 to 06:41 CET, 5.64 hours wall clock |
| Turns | 242 (median 65 s per turn) |
| API-equivalent cost | **$65.96** at list prices, $0.27 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 410K output, 227M cache read, 1.54M cache write, 2.4K uncached input |
| API requests | 1,223 (about 5.0 per turn) |
| Tool calls | 1,922, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 4 times (turns 96, 140, 188 and 229) |

Cache reads are 69% of the bill ($45.41), cache writes 19% ($12.34) and output 12% ($8.20). Turns 1 to 50 cost $6.17 (median 49 s a turn), 51 to 100 $13.00 (59 s), 101 to 150 $15.89 (78 s), 151 to 200 $14.85 (73 s), and 201 to the end $16.05 (68 s).

## How it went

On turn 1 Opus wrote its plan: "goal Culture victory. Plan: expand to 5-6 cities, wonders (France bonus to wonder production/tourism), Theater Squares, Chateaux later." The start was slow. A barbarian scout captured its first settler on turn 15 and the settler was gone when the scout died. At turn 50 France had 3 cities and 9 techs to the best AI's 15, last of 8 in score (54). By turn 100 it had 8 cities, the number it kept to the end, and was 5th (187).

From there culture took over. Opus built Theater Squares, art and artifact museums, Chateaux from turn 127, and wonders: the Colosseum, the Bolshoi Theatre, Broadway, Cristo Redentor, the Forbidden City, Mont St. Michel, the Eiffel Tower and Great Zimbabwe among nine. France was 1st in score at turns 150, 200 and 225, and its tourism grew from 78 a turn at turn 150 to 360 at turn 200 and 674 at the end (Egypt 790). Greece declared war on turn 176 and killed a trader near Rouen; Opus made peace on turn 188. Late in the game four barbarian submarines raided its coast, and Opus sank them with destroyers and artillery.

The game itself warned twice. On turn 205 it showed "Foreign Culture Victory Imminent", and on turn 220 "Your Culture Victory Imminent" and "Your Culture Dominant". civ6-mcp's victory report showed France far behind every civ instead, and Opus trusted it: "the tool may be inaccurate", but it judged a culture win "unlikely given the tourist gap". Read the game's way on the turn-240 save, France had 227 of the 310 visiting tourists it needed, and Egypt had 258 of the 283 it needed: Egypt, not France, was closest to a culture win.

Meanwhile Greece, with 68 techs, ran the space race: 1 of 5 projects on turn 202, 2 on turn 228, 3 on turn 235, 4 on turn 238 and the last on turn 242. Opus had renewed an alliance with Greece on turn 226. When Greece reached 3 projects it tried to stop it: a spy could not travel to any Greek city (turns 235 to 239), and its war declarations on turns 240, 241 and 242 were refused. By its own account an anti-tank crew already stood on the Ephesus spaceport, waiting for the war. Its other spy launched two Disrupt Rocketry missions against America in Washington. Greece finished the last Mars project on turn 242, and the game ended. In its closing summary Opus named its own mistakes: "I didn't treat Greece's space race as urgent early enough", and "I renewed the alliance with Greece at T226. That later blocked every option to stop them."

| Turn | Score (rank) | Cities | Techs (best AI) | Tourism / turn | Wonders |
|---|---|---|---|---|---|
| 50 | 54 (8th) | 3 | 9 (15) | 0 | 0 |
| 100 | 187 (5th) | 8 | 22 (34) | 0 | 0 |
| 150 | 340 (1st) | 8 | 38 (52) | 78 | 2 |
| 200 | 478 (1st) | 8 | 52 (68) | 360 | 6 |
| 242 | 554 (2nd) | 8 | 62 (68) | 674 | 9 |

## Final standings (turn 242)

| Civ | Score | Cities | Science / turn | Techs | Civics | Space projects | Tourism / turn | Domestic tourists |
|---|---|---|---|---|---|---|---|---|
| Egypt | 557 | 13 | 198 | 54 | 51 | 0 | 790 | 316 |
| **France (Opus 5.5)** | **554** | **8** | **206** | **62** | **51** | **1** | **674** | **286** |
| India | 501 | 10 | 231 | 68 | 37 | 1 | 150 | 71 |
| **Greece (winner)** | 493 | 12 | 240 | 68 | 39 | 5 | 20 | 54 |
| America | 478 | 10 | 189 | 62 | 41 | 3 | 132 | 88 |
| Sumeria | 466 | 14 | 206 | 59 | 50 | 0 | 370 | 141 |
| Brazil | 464 | 9 | 133 | 49 | 40 | 0 | 344 | 88 |
| Russia | 414 | 8 | 108 | 51 | 36 | 0 | 76 | 35 |

The diary row for turn 242 was read before Greece's last project; Greece's 5th is from the game-over screen.

## The harness in this game

From the run log, the agent's tool results and replays of the turn-240 save:

- **The culture count was wrong.** civ6-mcp's `get_victory_progress` compared, civ by civ, the tourists from that civ visiting France with that civ's domestic tourists ("Egypt counted 310 tourists from its own civ against only 46 from us"). The game counts all the tourists visiting a civ against the largest domestic count of any other civ (its World Rankings screen, `WorldRankings.lua`). So the report showed every civ out of reach while the game called France's culture win imminent, and it never showed that Egypt was 25 tourists from winning. Fixed from the next game: the report shows the game's count for the agent and each rival, and its Culture verdict uses it.
- **The wrong turn limit.** The same report said "SCORE (highest at turn 500)" in every game; this one ends at turn 250. Opus noted it on turn 160 and later planned for "a score win at T500". Fixed: the heading names the game's own limit (Online speed's 250 turns).
- **Refusals with no reason.** The game sends no spy into an ally's cities and allows no war on an ally or a declared friend, but civ6-mcp's answers were "it gave no reason" and "Possible reasons: friendship/alliance active, 10-turn peace cooldown, or target is invalid". On the turn-240 save, spy travel was refused to all 10 Indian and all 12 Greek cities (both allies) and allowed to every city of the other five civs, and `CanDeclareWarOn` was false for exactly the allies and declared friends. From the next game both answers name the alliance or friendship.
- **No excavation.** Opus bought an Archaeologist for 670 gold on turn 126 and found it could not excavate the antiquity site: civ6-mcp has no order for it ("excavation not possible via MCP tools — avoid archaeology"). It deleted the unit on turn 132 and gave up on artifacts. Not fixed yet.
- Smaller notes: during the war with Greece the agent's anti-tank crew could not pillage a Greek spaceport (turn 187, refused without a reason), and two friendship declarations came back `Error: INVALID|unknown` (turn 174, to Brazil, and turn 222, the second of two sent at once, to India, already a friend).
- No AI-turn hangs, no tool errors and no outside action during the game. At the very end the CLI reported that a transcript write failed because a disk on the dev server was full for a moment; the run's own record (turn rows, events, the archived transcript) is complete.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 243 is the agent's closing summary after the defeat screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150, 200 and 242 (game window on top, war room below).
