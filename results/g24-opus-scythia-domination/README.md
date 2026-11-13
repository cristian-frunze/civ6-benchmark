# Game 24: Opus 5.5 as Scythia on Prince, goal: Domination victory, Online speed

**Result: Domination victory on turn 149, 1st of 8 in score.** Game 24 is the first of three Opus 5.5 games (high effort) with other civs and other victory goals, after the user asked for them. Opus played Scythia (Tomyris), a civ built for war: it gets two Saka Horse Archers or Horsemen for the price of one. The map script, size, speed (Online, 250-turn limit), difficulty (Prince) and seed are the same as in the Sumeria games, in the base game with the playbook. Another leader changes the start and the AI civs: Scythia met Rome, Greece, Brazil, Germany, America, Egypt and Sumeria. The harness is game 23's plus the click fix for new starts. A helicopter took the last original capital, Rio de Janeiro, on turn 149, 20 turns sooner than game 4's Domination win as Sumeria (turn 169) and for less money.

| | |
|---|---|
| Played | 2026-11-13 12:36 to 19:40 CET, 7.06 hours wall clock |
| Turns | 149 (median 159 s per turn) |
| API-equivalent cost | **$82.02** at list prices, $0.55 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 606K output, 264M cache read, 2.15M cache write, 2.8K uncached input |
| API requests | 1,396 (about 9.4 per turn) |
| Tool calls | 1,871, 1 returned an error (below) |
| Claude Code sessions | 1, with no usage limits and no interventions; it compacted its context 6 times (turns 57, 80, 104, 120, 133 and 146) |

Cache reads are 64% of the bill ($52.70), cache writes 21% ($17.18) and output 15% ($12.13). The turns got slower and dearer as the army grew: turns 1 to 50 cost $11.53 (median 80 s a turn), 51 to 100 $26.01 (163 s) and 101 to 149 $44.48 (221 s). Scythia had 24 units at turn 50, 42 at turn 100 and 100 at the end.

## How it went

| Turn | Original capital taken |
|---|---|
| 44 | Aachen (Germany, eliminated) |
| 55 | Uruk (Sumeria, eliminated) |
| 91 | Râ-Kedet (Egypt) |
| 114 | Sparta (Greece, eliminated on turn 115) |
| 133 | Rome (Rome) |
| 138 | Washington (America, eliminated) |
| 149 | Rio de Janeiro (Brazil) |

On turn 1 Opus read Scythia's kit and wrote the plan it then followed: "expand to 4-5 cities, then mass horse units to take nearest capital." It researched Animal Husbandry and Horseback Riding first, found Germany's and Sumeria's capitals by turn 25, each a one-city civ close by, and declared a surprise war on Germany on turn 32 with Saka Horse Archers. Berlin fell on turn 38 and Aachen on turn 44, and Germany was out. Uruk followed on turn 55, and Sumeria was out too. It kept settling between wars: 7 cities at turn 50, when it was already 1st in score (113, Egypt 96).

Egypt was next. Opus declared war on turn 62, lost a horse archer and captured a settler, and on turn 70 Egypt sued for peace: a Great Work, 67 gold and 27 gold a turn for 30 turns. Opus took the deal, upgraded to crossbows, trebuchets and knights, and declared war again on turn 79. Shedet fell on turn 85 and Egypt's capital, Râ-Kedet, on turn 91. At turn 100 Scythia had 15 cities, 379 points to America's 185, and 35 techs to the best AI's 31.

Greece fell in ten turns to cavalry, field cannons and artillery: war on turn 105, then Athens (107), Corinth (108), Sparta and Mycenae (114) and Eretria (115). Opus first took Athens for Greece's capital; Sparta was the original one. America came next. Its first declaration, on turn 115, did not take effect (below), so the war started on turn 116. New York, the American city in reach, fell on turn 121 and was not the capital; Opus turned down America's offer of gold for peace on turn 131 ("I need their capital") and took Washington on turn 138. Rome, at war from turn 123, lost its capital on turn 133 and was down to one city by turn 139.

Brazil was the last and the hardest to find. Opus sent embarked scouts west and east on turn 139, found Rio de Janeiro on turn 142 across a strait in the west (pop 13, walls), declared war and sent the whole army there by sea: tanks, artillery, field cannons, cavalry and helicopters. On turn 149 artillery and a field cannon brought Rio's walls to 106/300 and its garrison to 74/200, and a helicopter took the city. The game ended that turn on a Conquest victory, the game's own name for Domination. Opus was by then also the science leader by far (404 a turn to Brazil's 28, 59 techs to 32), with 34 cities.

## Final standings (turn 149)

| Civ | Score | Cities | Science / turn | Techs | Civics | Military |
|---|---|---|---|---|---|---|
| **Scythia (Opus 5.5, winner)** | **880** | **34** | **404** | **59** | **37** | **3,357** |
| Brazil | 239 | 5 | 28 | 32 | 21 | 126 |
| Rome | 158 | 1 | 14 | 24 | 29 | 44 |
| Egypt | 132 | 1 | 10 | 24 | 25 | 259 |
| Germany, Sumeria, Greece, America | eliminated on turns 44, 55, 115 and 138 | | | | | |

## Scythia and Sumeria, both on Domination

| | Game 4 (Sumeria) | **Game 24 (Scythia)** |
|---|---|---|
| Result | Domination victory, turn 169 | **Domination victory, turn 149** |
| First capital taken | Madrid, turn 42 | **Aachen, turn 44** |
| Turn 50: score / cities / military | 91 / 5 / 224 | **113 / 7 / 415** |
| Turn 100: score / cities / military | 352 / 15 / 1,104 | **379 / 15 / 1,301** |
| Turn 149: score / cities / military | 773 / 28 / 2,901 | **880 / 34 / 3,357** |
| Cost (per turn) | $100.64 ($0.60) | **$82.02 ($0.55)** |
| Wall clock (median per turn) | 7.6 h (125 s) | **7.06 h (159 s)** |
| API requests / tool calls (errors) | 1,839 / 2,526 (9) | **1,396 / 1,871 (1)** |

The two games played on the same map script and seed, but not against the same AIs or from the same start, so the comparison is loose. Both took their first capital in the early 40s and had 15 cities at turn 100. Scythia was ahead at turn 50 on cities and army, took the last four capitals in 35 turns (114 to 149) where Sumeria needed 39 (130 to 169), and finished 20 turns sooner.

## The harness in this game

From the run log and the agent's tool results:

- **War declarations.** All 9 of Opus's war declarations came back `WARN:WAR_UNCERTAIN|... session completed but war state not yet confirmed`: civ6-mcp reads the war state in the same frame it closes the diplomacy session, before the game has committed the war. Eight took effect as sent. The one on America on turn 115 did not: the next turn's attack on New York came back `NOT_AT_WAR`, and Opus declared again ("The first America war declaration on T115 failed silently"). That cost about a turn. Still open: read the war state again after the session and say plainly whether the war is on.
- **One tool error**, on turn 27: Opus answered a trade with `{"other_player_id": 7, "accept": True}`, Python's `True` instead of JSON's `true`, and Claude Code refused the call; the next call worked. civ6-mcp's end-turn message spells the call `respond_to_trade(other_player_id=X, accept=True/False)`.
- **Many units, many end turns.** Opus called `end_turn` 280 times in 149 turns. 37 of the extra calls came back because units on multi-turn moves arrived as the turn ended and needed orders again, the game's own rule; from turn 122, with about 60 units, Opus skipped each unit by id before ending the turn.
- No AI-turn hangs, no tool-name errors after its 6 compactions, and no outside action during the game.
- The new start's BEGIN GAME click: the start save for this game was made with `remote/make-start.sh`, but the Arabia and France starts after it failed until `windows/click-at.ps1` started each click 40 px away. The click had left the cursor on the button, and the game takes a click only on a button it saw the mouse move onto.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 150 is the agent's closing summary after the victory screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100 and 149 (game window on top, war room below).
