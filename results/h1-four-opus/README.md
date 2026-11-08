# Hotseat game h1: four Opus 5.5 agents and four built-in AI civs, Online speed

**Result: Science victory on turn 157 by Rome (Opus-B).** Four Opus 5.5 agents (high effort), each its own Claude Code session, played Sumeria, Rome, Greece and Brazil in one hotseat game. The built-in AI played Germany, America, Egypt and Spain on Prince. Map: standard Pangaea, same seed as games 3 and 4, Online speed, 250-turn limit, base game, playbook, no assigned goal. Each agent knew other agents were in the game, but not which civs they played.

| | |
|---|---|
| Played | 2026-11-07 17:19 to 2026-11-08 05:30 UTC, 12.2 hours wall clock |
| Turns | 157 rounds, 634 seat turns (median 48 s each; a whole round took a median 216 s) |
| API-equivalent cost | **$277.02** for all four seats at list prices (Opus 5.5: $4 / $20 per MTok in / out, $0.20 cache read, $8 cache write with the 1-hour TTL) |
| Tokens | 1.40M output, 831M cache read, 10.3M cache write, 10K uncached input |
| API requests | 5,762 (about 9.1 per seat turn) |
| Claude Code sessions | one per seat, resumed once per turn, each on its own subscription account |

Cache reads are 60% of the bill ($166.14), cache writes 30% ($82.77), output 10% ($28.07).

## The four agents

| Seat | Civ | Score at turn 157 | Cities | Science / turn | Techs | Military | Cost | Median s / turn | Retries |
|---|---|---|---|---|---|---|---|---|---|
| Opus-C | Greece | **568** (1st) | 12 | 162 | 53 | 781 | $80.84 | 53 | 0 |
| **Opus-B** | **Rome** | 489 (2nd) | 11 | **523** | **68** | 481 | $64.48 | 48 | 3 (turn 157, after the win) |
| Opus-D | Brazil | 476 (3rd) | 9 | 256 | 65 | 605 | $68.40 | 48 | 5 (all forced by AI-turn hangs) |
| Opus-A | Sumeria | 394 (5th) | 9 | 409 | 60 | 421 | $63.31 | 43 | 0 |

The AI civs: Germany 409 (4th), America 310, Spain 231, Egypt 214. Nobody was eliminated and no city changed hands between majors.

## How it went

The four agents pulled away from the AI early and stayed ahead. Average score, agents against AI civs:

| Turn | Agents | AI civs |
|---|---|---|
| 25 | 39 | 34 |
| 50 | 105 | 74 |
| 100 | 303 | 175 |
| 157 | 482 | 291 |

Rome and Greece traded the score lead about 20 times between turns 25 and 94; Greece then led to the end on the widest empire with the most civics (48). Rome led in science from turn 75 to the end (apart from turns 147-148, when it switched to Communism) and built for space.

Three agents raced for a science win, and they spied on each other:

- **Turn 130:** Brazil finished the first Spaceport. Rome's came on turn 132, Sumeria's on 142.
- **Turn 138:** Brazil had 2 of 5 space projects, Earth Satellite and the Moon Landing, which Great Scientist Carl Sagan finished outright. Rome had 1.
- **Turns 144-155:** the race went 2-2, then Rome 3-2 (Mars Reactor, turn 153), then 3-3. Rome sent spies against Brazil's Spaceports; Brazil bought spies to guard them after enemy spies sabotaged two of its Industrial Zones.
- **Turn 156:** Rome went 4-3 and recruited Great Engineer Sergei Korolev, who adds 1,500 production to a space project.
- **Turn 157:** Rome moved Korolev to Antium's Spaceport and activated him, which finished Mars Hydroponics, the fifth project. Brazil was at 3 of 5 with its win projected around turn 162. Sumeria was at 1.

The AI civs declared war on the agents five times (America and Spain on Greece, turn 64; Egypt and America on Rome, turn 79; Germany on Greece and Sumeria, turns 106-107; America on Brazil, turn 122). No agent declared war on another agent.

## The ending, and how we confirmed it

A win that comes in the middle of a hotseat turn freezes the game: every unit order fails, and through the MCP Bridge no victory screen shows. Rome's agent could not end turn 157 and the runner, which looked for a winner only at the start of a round, gave up after 4 tries ("did not end turn 157"). The three extra tries cost $1.81.

After the run stopped we loaded the save made at the start of Rome's turn 157 (`TRAJAN 157 1884 AD MCP`) and repeated the agent's two orders: move Korolev to (34,37) and activate him. `Game.GetWinningTeam()` went from -1 to Rome's team, and the game played the science victory cinematic ([`shots/T0157-win-replay.jpg`](shots/T0157-win-replay.jpg), with the war room below it). `tools/run_hotseat.py` now checks for a winner after every seat turn.

## Harness incidents and interventions

- **The AI civs' turn hung five times**, each time right after Brazil (Opus-D, the last agent seat) ended its turn: turns 53, 93, 111, 120 and 141. The game sat on the turn-change screen with no Lua error and no open diplomacy. Reloading the save from the start of Brazil's turn fixed it every time: Brazil replayed the turn and the AI civs then finished in seconds. The first reload was by hand (turn 53, after 49 minutes); after that `tools/hotseat_doctor.py` did it by itself after 20 idle minutes. Brazil's replayed turns cost $2.78 and its orders from the hung turns were undone, a small handicap for Brazil.
- **Turn 157:** the mid-turn win above.

Every action on the running game from outside the agents is in [`interventions.jsonl`](interventions.jsonl).

## Files

- [`game.json`](game.json): settings and seats.
- [`turns.jsonl`](turns.jsonl): one row per seat turn with seconds, API requests, tokens, API-equivalent dollars, tries and the agent's closing message.
- [`rounds.jsonl`](rounds.jsonl): one row per round with every major civ's score, cities, yields, techs, civics and military, and the winning team. The last row is the start of turn 157, before the win.
- `diary.jsonl.gz`: civ6-mcp's per-turn rows for every civ, from the four agents' views.
- [`interventions.jsonl`](interventions.jsonl): every action on the running game from outside the agents.
