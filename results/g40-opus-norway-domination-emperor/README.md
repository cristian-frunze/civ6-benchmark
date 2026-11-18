# Game 40: Opus 5.5 as Norway on Emperor, goal: Domination

**Result: Defeat on turn 187. Germany (AI) won a Science victory.** Opus 5.5 (high effort) played Norway (Harald Hardrada) on Emperor against seven AI civs: Russia, Egypt, Germany, Greece, America, Sumeria and Brazil. It was the first game with a goal other than Science above Prince, one level above King, where Opus lost both of its Science games (20 and 21, as Sumeria). Map script, size, speed (Online, 250-turn limit) and seed are the same as in the earlier games, and the leader changes the start and the rivals. Norway finished tied 4th of 8 in score (515, with Greece; Russia led with 645), with 18 cities and the largest army, and it held one rival capital, Rio de Janeiro, when Germany's last space project landed. Opus had won all five earlier Domination games, all on Prince. The harness had the fixes from games 37 and 38.

| | |
|---|---|
| Played | 2026-11-18 02:52 to 08:14 CET, 5.36 hours wall clock (the run waited about 32 minutes before that for launch pacing on the busy dev box) |
| Turns | 187 (median 80 s per turn) |
| API-equivalent cost | **$66.21** at list prices, $0.35 a turn (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 445K output, 232M cache read, 1.35M cache write, 2.4K uncached input |
| API requests | 1,189 (about 6.4 per turn) |
| Tool calls | 1,667, none returned an error |
| Claude Code sessions | 1, with no usage limits and no interventions. It compacted its context three times (turns 88, 129 and 165) |

Cache reads are 70% of the bill ($46.48), cache writes 16% ($10.82) and output 13% ($8.90). Turns 1 to 50 cost $6.21 (median 45 s a turn), 51 to 100 $17.07 (77 s), 101 to 150 $20.63 (98 s) and 151 to the end $22.21 (170 s): the wars and the 18-city empire of the last 37 turns took a third of the bill.

## How it went

Opus's turn-1 plan: "Norway, Emperor, Pangaea. Goal domination. Plan: expand to 4-6 cities, then early military push (archers/swords, later Berserkers via Military Tactics). Longships from Sailing for coastal harass." It took God of the Sea as its pantheon on turn 24 and never founded a religion, and it moved from Chiefdom to Classical Republic (turn 51) and Merchant Republic (108). It settled 9 cities by turn 82, more than any rival, but it was last in score through turn 75, with 11 techs at turn 50 to Greece's 21 and a science of 25 at turn 60 to Sumeria's 67.

**Three offensives that failed.** On turn 88 Opus declared a surprise war on Brazil, the weakest civ (military 113 to Norway's 405), to take Manaus and then Rio. The army had to walk around Jerusalem and Sumeria's borders, and on turn 98 Germany (military 675) declared war. Opus lost a Berserker and a ram to a German stack on turn 104 ("Our eastern push failed. Pivot: economy"), made peace with Germany on turn 107, and tried five times on turns 107, 108 and 133 to declare war on the city-state Jerusalem, which stood between its army and Brazil. All five came back `WAR_NOT_DECLARED`, a harness bug fixed after this game. It then marched into Russia (military 149 at turn 110), found Russia had declared war first (turn 115), and on turn 117 hit St. Petersburg's Renaissance walls: "crossbow and berserker+ram did only 1-2 dmg. Assault infeasible with current tech." Peace came on turn 122. A second Russian war with Field Cannons and Artillery (turns 137 to 147) lost two Berserkers and an Artillery to the city and Russia's own Artillery, and Russia fielded a Tank by turn 144. Opus took peace with Russia and Brazil on turn 147.

**The pivot.** On turn 148 it found 1,245 gold unspent ("spend it"), bought two Settlers and founded five more cities on turns 150 to 165, built Industrial Zones and Commercial Hubs, and ran 8 trade routes, most of them to Geneva. Its income went from +4 gold a turn at turn 100 to +155 at turn 150.

**The last war.** From turn 164 Opus massed seven Artillery and bought Bombers ("Bombers are the key siege weapon (~85 wall dmg/strike vs artillery 24)", turn 171). It took Manaus and Fortaleza on turn 173, Rio de Janeiro, Brazil's capital, on turn 180, and Sumeria's Adab on turn 183, and took peace from Brazil (80 gold and 50 a turn) and Sumeria (26 a turn) to turn on Germany. On turn 175 Norway's military was 2,036, the largest by 750.

**The space race it watched.** Opus saw the threat on turn 128: "Germany reports 1 spaceport and 1/5 space projects (with only 43 techs?) - monitor ... we must eventually capture Berlin to stop it," and its tooling note said the readout "may be anomaly." It fought Russia instead. Germany reached 2 of 5 on turn 161, 3 on 176 and 4 on 183, and Greece 3 of 5 by turn 172. Opus declared war on Germany on turn 183, sent a spy to disrupt rocketry in Greece's Argos (its turn-182 note: "Spy in transit to Argos"), and on turn 187 had three Jet Bombers at Rio and Manaus, with its plan to "scout Cologne with infantry for vision so bombers can hit city." Germany won that turn. Its bombers had been refused against Cologne and Ulm on turns 183 to 185 with an error that did not say why; the reason was that the cities were out of sight (see the harness section).

| Turn | Score (rank) | Cities | Science / turn | Techs (most of any AI) | Military (rank) | Gold / turn |
|---|---|---|---|---|---|---|
| 50 | 81 (8th) | 6 | 19 | 11 (Greece 21) | 177 (4th) | +20 |
| 100 | 214 (7th) | 9 | 97 | 32 (Sumeria 41) | 552 (3rd) | +4 |
| 150 | 321 (7th) | 10 | 202 | 47 (Sumeria 61) | 780 (2nd) | +155 |
| 175 | 437 (6th) | 16 | 188 | 54 (Sumeria 68) | 2,036 (1st) | +126 |
| 187 | 515 (4th) | 18 | 203 | 59 (Germany, Sumeria 68) | 2,020 (1st) | +69 |

## Final standings (turn 187)

| Civ | Score | Cities | Science / turn | Techs | Military | Space projects |
|---|---|---|---|---|---|---|
| Russia | 645 | 14 | 400 | 67 | 1,206 | 1 |
| Egypt | 577 | 13 | 147 | 50 | 1,001 | 0 |
| **Germany (winner)** | **568** | **11** | **221** | **68** | **1,412** | **4, then the last** |
| Norway (Opus 5.5) | 515 | 18 | 203 | 59 | 2,020 | 0 |
| Greece | 515 | 10 | 204 | 64 | 460 | 3 |
| America | 466 | 10 | 244 | 59 | 925 | 1 |
| Sumeria | 459 | 10 | 275 | 68 | 331 | 1 |
| Brazil | 214 | 3 | 21 | 38 | 2 | 0 |

## Against the earlier Domination and Emperor games

| Game | Civ, goal, level | Result | Cost | Hours |
|---|---|---|---|---|
| 4 | Sumeria, Domination, Prince (one Opus of four) | Domination victory, turn 169 | - | - |
| 24 | Scythia, Domination, Prince | Domination victory, turn 149 | $82.02 | 7.1 |
| 28 | Aztecs, Domination, Prince | Domination victory, turn 122 | $57.57 | 5.1 |
| 34 | Japan, Domination, Prince | Domination victory, turn 236 | $87.65 | 8.4 |
| 37 | Rome, Domination, Prince | Domination victory, turn 176 | $69.47 | 7.8 |
| 20 | Sumeria, Science, Emperor | Defeat (America, Science), turn 186; last of 8 | $47.67 | 4.5 |
| 21 | Sumeria, Science, Emperor (game 20 repeated) | Defeat (Greece, Science), turn 169; last of 7 | $38.83 | 3.6 |
| 40 | Norway, Domination, Emperor | Defeat (Germany, Science), turn 187; tied 4th of 8 | $66.21 | 5.4 |

Each civ had its own start and rivals, so the games compare loosely. On Prince the five Domination wins took 122 to 236 turns. On Emperor the AI civs had about twice Norway's techs at turn 50 (Greece 21 to 11), Renaissance walls when its Berserkers reached St. Petersburg (turn 117), and a Tank and Helicopters by the time its Artillery arrived; Norway took its first rival capital on turn 180. Game 40 still finished higher than both Emperor Science games, which ended last.

## The harness in this game

From the run log and the agent's tool results and tooling notes:

- **War on a city-state never took (fixed after this game).** Five declarations of war on Jerusalem (turns 107, 108 and 133) came back `WAR_NOT_DECLARED`: civ6-mcp sends a war declaration through a diplomacy session, which the game opens only with full civs. The harness now declares war on a city-state the way the game's own war popup does (`DeclareWarPopup.lua`: the `DIPLOMACY_DECLARE_WAR` player operation). Replayed from turn 107's save, the same call put Norway at war with Jerusalem.
- **Air strikes refused without a reason (fixed after this game).** Bombers were refused against Rio (turn 174) and against Cologne and Ulm (turns 183 to 185) with `ATTACK_BLOCKED ... at ({target_x},{target_y}) ... not adjacent`: the air strike was not allowed, so civ6-mcp tried a melee move, and its message kept a placeholder in place of the tile. Replayed from turn 184's save, the game refused an air strike on any tile not in sight (Cologne was 8 tiles from the bomber and Ulm 5, both in its range of 10, neither in sight), and gives no reason. The harness now says why: no moves left, out of range (with "rebase it closer"), or not in sight ("move a unit within sight of it first"). Opus worked the visibility rule out by itself on turn 187, the last turn.
- **Siege estimates and a siege shot after moving (fixed after this game).** civ6-mcp's combat estimate reads only a unit's ranged strength, and siege units and bombers have a bombard strength instead, so 21 estimates for Artillery and Bombers were labelled "Melee" with the unit's melee strength and a damage to the attacker; three Artillery shots at helicopters were flagged "WARNING: attacker likely dies!", and the Artillery took no damage. On turn 142 an Artillery that had moved, which a siege unit cannot fire after, was sent into St. Petersburg as a melee move and came back `NOT_MOVED`. The estimate now carries the game's own combat preview (the attack screen's `CombatManager.SimulateAttackVersus`), and a siege unit that cannot fire says why. Replayed from turn 166's save, an Artillery shot at a Cavalry was previewed at 15 damage and dealt 15; civ6-mcp had estimated 21, as melee.
- **City attacks named the city.** Attacks on six cities (Manaus, Fortaleza, Rio de Janeiro, Adab, St. Petersburg and Ulm) named the city centre and reported its walls and garrison after each hit, as the game 37 fix intended. Bombers took about 85 off the walls a strike (Manaus on turn 171, Rio on turn 179), Artillery about 24.
- **Aircraft rebased.** Five rebases went through and one was refused with the bases in range listed, as the game 37 fix intended.
- **War declarations on full civs settled.** All five (Brazil twice, Russia, Sumeria and Germany) came back `WAR_DECLARED` from the game's war state.
- **Refusals by the game's rules.** 50 orders were refused because a unit of the same formation class held the tile or the city (a purchase of Artillery in Karmøy was blocked by an AT Crew), each naming the unit; 88 moves reported moves left instead of "moves exhausted".
- **Still open:** production refusals give no reason (turn 117: "UNIT_LINE_INFANTRY cannot start", while upgrades to Line Infantry worked), four trade routes were refused with no reason, and a deal summary listed "Joint War (20 turns)" without the target (turn 176; Opus turned the deal down for that reason).
- No skipped turns, no AI-turn hangs, no tool errors and no outside action during the game.

## Files

- [`turns.jsonl`](turns.jsonl): one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, and the agent's five reflections. Row 188 is the agent's closing reply after the defeat screen.
- `diary.jsonl.gz` and `diary_cities.jsonl.gz`: civ6-mcp's per-turn rows for every civ and for every city.
- [`shots/`](shots/): the screens at the start of turns 50, 100, 150 and 187 (game window on top, war room below).
