# Game 27: Opus 5.5 as France on Prince, goal: Culture victory, fixed harness

**Result: Culture victory on turn 195, 1st of 8 in score.** Game 27 replays game 26 on the same start. Opus 5.5 (high effort) plays France (Catherine de Medici) against the same seven AI civs (Russia, India, Brazil, Greece, America, Egypt and Sumeria). The map, speed (Online, 250-turn limit), difficulty (Prince), seed and prompt are game 26's. Only the harness changed, with the fixes from game 26's write-up:

- `get_victory_progress` and end_turn's 10-turn victory snapshot count culture the game's way.
- Refused war declarations and spy travel name the alliance behind the refusal.
- Apostles can fight.
- Archaeologists can excavate.

Game 26 lost to Greece's Science victory on turn 242, with France 2nd in score. Game 27 won 47 turns earlier, for $14.68 less: the benchmark's first Culture victory.

| | |
|---|---|
| Played | 2026-11-14 08:00 to 12:35 CET, 4.58 hours wall clock |
| Turns | 195 (median 64 s per turn) |
| API-equivalent cost | **$51.28** at list prices, $0.26 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 296K output, 186M cache read, 1.03M cache write, 2.0K uncached input |
| API requests | 997 (about 5.1 per turn) |
| Tool calls | 1,416, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context twice (turns 87 and 145) |

Cache reads are 72% of the bill ($37.15), cache writes 16% ($8.21) and output 12% ($5.91). Turns 1 to 50 cost $7.09 (median 46 s a turn), 51 to 100 $15.21 (79 s), 101 to 150 $14.79 (65 s), and 151 to the end $14.18 (105 s).

## How it went

On turn 1 Opus wrote the same plan as in game 26: "Culture victory plan: expand to 5-6 cities, Theater Squares, wonders, later Chateaux." The start went better this time. No settler was lost: barbarians captured a builder, which Opus took back. France had 4 cities at turn 50 (game 26: 3) but was still last in score (68). By turn 100 it had 9 cities and was 2nd (225).

This time Opus went for archaeology. On turn 100 it planned "Natural History → Archaeological museums plus archaeologists for 3 antiquity sites". Lyon's Archaeological Museum was done on turn 115, and Opus bought an Archaeologist the same turn (680 gold). It excavated six sites between turns 116 and 141 and filled two museums, Lyon's (turn 121) and Toulouse's (turn 141). The game retires an Archaeologist once its museum is full, as Opus noted on turn 121. Great writers, artists and musicians filled the theater buildings, and six wonders added double tourism under France's ability: the Bolshoi Theatre (turn 134), the Hermitage (152), Cristo Redentor (177), Big Ben (191) and Great Zimbabwe among them. France's tourism was 278 a turn at turn 150 (game 26: 78), and France led in score on every turn from turn 150 to the end.

Greece declared war on turn 155, killed two traders, besieged Rouen and took it. Opus held Amboise and the rest with walls, Field Cannons and city strikes, and the war was over by turn 167, with Rouen still Greek. Sumeria started the space race: 1 of 5 projects by turn 170 and 2 by the end. Opus sent a spy to disrupt its rocketry in Uruk. America and India declared war in the last turns, and American Modern Armor reached Marseille on turn 195. Opus bought walls and an anti-tank crew (1,065 gold) to hold it.

end_turn printed the culture count every 10 turns, and Opus tracked it: "59/113 visiting tourists (+23 in 10 turns) ... At this rate we win around T215-225" on turn 170, then "89/120 visiting tourists (+30 in 10 turns!) ... we win around T193" on turn 180. On turn 195, `get_victory_progress` gave "You: 137 visiting tourists, need 136 (one more than Egypt's 135 domestic): you meet it", and the game ended on a Culture victory that turn.

| Turn | Score (rank) | Cities | Techs (best AI) | Tourism / turn | Wonders |
|---|---|---|---|---|---|
| 50 | 68 (8th) | 4 | 11 (14) | 0 | 0 |
| 100 | 225 (2nd) | 9 | 26 (31) | 32 | 0 |
| 150 | 389 (1st) | 9 | 40 (44) | 278 | 2 |
| 195 | 500 (1st) | 8 | 50 (56) | 572 | 6 |

## Final standings (turn 195)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military | Tourism / turn | Domestic tourists |
|---|---|---|---|---|---|---|---|---|
| **France (Opus 5.5, winner)** | **500** | **8** | **114** | **50** | **51** | **608** | **572** | **210** |
| America | 484 | 11 | 164 | 55 | 37 | 870 | 57 | 104 |
| Greece | 431 | 11 | 157 | 55 | 32 | 241 | 140 | 73 |
| Sumeria | 427 | 13 | 191 | 56 | 38 | 487 | 188 | 112 |
| Brazil | 387 | 8 | 63 | 41 | 38 | 670 | 117 | 114 |
| Russia | 356 | 10 | 65 | 41 | 28 | 520 | 60 | 32 |
| India | 330 | 8 | 170 | 47 | 27 | 175 | 70 | 72 |
| Egypt | 324 | 7 | 53 | 37 | 43 | 904 | 140 | 135 |

The game ranks culture by visiting tourists, not the domestic count in the last column. France's 137 visiting tourists beat Egypt's 135 domestic, the largest domestic count of any other civ.

## Game 26 and game 27

Both games used the same start. The difference has two parts, and one pair of games can't separate them. Opus played differently from the start: 4 cities at turn 50 instead of 3, and no settler lost. Earlier games show this kind of spread. Game 3 and its exact repeat, game 7, won Science 6 turns apart. The harness changes hit exactly what game 26 lacked:

- **The culture count.** In game 26 the report showed France out of reach while the game called its win imminent. Opus judged a culture win "unlikely given the tourist gap". In game 27 the count was right from turn 9, and Opus planned its last 30 turns on it.
- **Archaeology.** Game 26 deleted its Archaeologist. Game 27 dug up six artifacts.

## The harness in this game

From the run log and the agent's tool results:

- **The fixes from game 26 ran as intended.** The culture count came from the game's own rule in every 10-turn snapshot and in all 3 `get_victory_progress` calls. Excavation worked on all 6 sites. Five were battle sites, where the game asked whose artifact it was: Opus picked from the listed civs, and each pick went into a museum slot. The research check answered `NOT_AVAILABLE|TECH_MACHINERY cannot be researched yet: it needs Iron Working first` once (turn 76). No war declaration or spy trip was refused, and no religious unit fought.
- **A maintenance figure misread as units.** civ6-mcp's overview printed "Maintenance: -124 (units: 34)" beside "Units: 19". The 124 is the game's total upkeep for buildings, districts and units. The 34 is gold, the units' upkeep at list price. On turn 189 Opus read it as "34 units when I only have 19, so there are phantom units draining 124 gold per turn", and it repeated that in its closing summary. Fixed from game 29: the line names the 34 as gold.
- **A production switch reported as a completion.** When Ballistics came in on turn 159, the game switched Rouen's and Rheims's Crossbowman production to the Field Cannon that replaces it. civ6-mcp's turn report said "Rouen finished building UNIT_CROSSBOWMAN. Now: UNIT_FIELD_CANNON", and Opus noted "Units reported as built in the event log were missing from get_units". Fixed from game 29: a change along a unit's upgrade line, with no unit of the old type built, is reported as the game's switch.
- No AI-turn hangs, no tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 196 is the agent's closing summary after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 195 (game window on top, war room below).
