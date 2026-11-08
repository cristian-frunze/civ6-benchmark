# civ6-benchmark

How well does Claude Opus 5.5 play Sid Meier's Civilization VI?

This repo holds the setup, harness glue and results for running LLM agents in real Civ 6 games. It was inspired by Dwarkesh Patel's [Blood on the Clocktower benchmark](https://www.dwarkesh.com/p/clocktower). The game itself is driven by [lmwilki/civ6-mcp](https://github.com/lmwilki/civ6-mcp) (MIT), an MCP server that talks to Civ 6 through its built-in FireTuner debug port. That is the same harness the CivBench paper used ([arXiv 2609.02459](https://arxiv.org/abs/2609.02459)).

## Experiments

| # | Setup | Status |
|---|---|---|
| 1 | Opus 5.5 (high effort) vs the built-in AI on Pangaea, standard size, Quick, Prince, **with** the civ6-mcp playbook | **Science victory, turn 262**, $67.83 API-equivalent ([results](results/g1-standard/)) |
| 2 | Same map, **rules only**, no strategy playbook | **Science victory, turn 266**, $72.32 API-equivalent, about $7 of it in two harness stalls ([results](results/g2-baseline/)) |
| 3 | Assigned victory goal (Science, then Domination), Online speed (250-turn limit), same seed and civs. Every victory type stays on, and any win counts; we also record whether it matched the goal | **Science goal: Science victory, turn 212** of 250, $56.43 ([results](results/g3-science/)). **Domination goal: Domination victory, turn 169**, $100.64, 34 cities at the end ([results](results/g4-domination/)) |
| 4 | Opus vs Opus on a standard 8-civ map, Online speed: (A) 1 Opus + 7 AI vs (B) 4 Opus + 4 AI, same seed and civs, both as hotseat games so the map is the same | **(B) 4 Opus + 4 AI: Science victory on turn 157 by Rome, an Opus seat**, $277.02 for all four seats, 12.2 hours. The four agents averaged 482 score to the AI civs' 291, and three of them raced for space ([results](results/h1-four-opus/)). **(A) 1 Opus + 7 AI: Science victory on turn 168**, $78.02, 2.9 hours, no interventions; on the same map it played far stronger than game 3 (score 268 to 185 and 36 techs to 27 by turn 100) and won 44 turns earlier ([results](results/h2-one-opus/)) |
| 5 | Game 3's setup (Science goal, Online) on **Deity**, the hardest level, instead of Prince | **Defeat: Greece (AI) won a Science victory on turn 144**; Opus finished last (score 218 to the AI's 415-549, 37 techs to Greece's 68), $37.80 ([results](results/g5-deity-science/)) |
| 6 | Game 3's setup with **Sonnet 5.5** (high effort) instead of Opus 5.5 | **Science victory, turn 223** (Opus: 212), $58.70 (Opus: $56.43): half the token price, but cache reads cost the same and were 85% of the bill ([results](results/g6-sonnet-science/)) |
| 7 | Game 3 **repeated** exactly (same start, same prompt, same harness), to see how much one game varies from the next | running |
| 8 | Game 3's setup with Opus 5.5 at **medium effort** (Claude Code's default) instead of high, on the fixed harness (below) | queued after game 7 |
| 9 | Game 3's setup with **Fable 5.1** (high effort), on the fixed harness | queued after game 8 |
| 10 | Game 3 repeated on the **fixed harness** (Opus 5.5, high effort): the baseline for games 8 and 9, and a measure of the fix | queued after game 9 |

All games use the **base game** ruleset (no Rise and Fall or Gathering Storm), so there's no diplomatic victory, and results don't compare directly with CivBench, which used Gathering Storm.

Every game reports API-equivalent cost: input, output, cache-read and cache-write tokens, priced at list API rates, even though runs use Claude subscriptions.

## Harness

Each agent is Claude Code in headless mode (`claude -p`) with the civ6-mcp tools and nothing else: no shell, files, web, CLAUDE.md, memory, hooks or skills (`tools/run_game.py` has the flags). Its system prompt is the CivBench playbook (or CivBench's minimal baseline for the rules-only game), plus three notes in [`prompts/`](prompts/): what the base game lacks, the batch tools below, and that nobody is watching. One line of the subscription's organization instructions still reaches the model; it is about connecting apps and has nothing to do with Civ.

Four changes to stock civ6-mcp, all in `windows/civ_mcp_http.py`:

- **Base game.** civ6-mcp targets Gathering Storm. Its Lua is rewritten on the fly to call `CB_` stand-ins for expansion APIs (`lua/base-game-compat.lua`), which return neutral values when the base game lacks them. Tools for systems the base game doesn't have (governors, dedications, World Congress) are removed.
- **Batch tools.** A model step takes much longer than a tool call (0.3-1.5 s), so agents get `get_turn_briefing` (overview, units, cities and notifications in one call) and `issue_orders` (a list of unit, city and research orders in one call). Every inner call is still logged as its own tool call.
- **One shared tuner connection** over HTTP, see [setup](docs/setup.md).
- **No unplayed turns after a diplomacy pause** (from game 8). When an AI civ opens a proposal during the AI turn, civ6-mcp tells the agent to answer it "then end_turn again", but by then the agent's next turn has begun, and agents ended 0 to 14 turns per game without playing them (`tools/turn_trap.py`). `end_turn` now reports the new turn instead, see [setup](docs/setup.md).

## What each game records

`tools/run_game.py` starts `tools/archive.py` next to the agent, which keeps a complete record of the game in the run directory:

- **Every tool call** with its full parameters and result, timing and turn (civ6-mcp's log).
- **Every turn**: a row per civilization (score, yields, cities, techs, military, religion, ...) and the agent's five reflections (tactical, strategic, tooling, planning, hypothesis).
- **The agent's reasoning**: each Claude Code session's transcript and stream, with thinking summaries (`--thinking-display summarized`), messages, tool calls and results, and token usage for API-equivalent cost.
- **A screenshot** of the screens at the start of each turn, and **every autosave**, so any turn can be reloaded.
- Per-turn map ownership deltas and city snapshots, for replays.
- **A turn-by-turn timeline** joining all of the above (`tools/timeline.py`, rebuilt after every sync): `timeline.jsonl` has every thought, message, tool call and result tagged with its turn; `turns.jsonl` has one row per turn with seconds, API requests, tokens, API-equivalent dollars, tool calls and errors, the reflections and the diary stats; `timeline.md` is the readable version.
- **Interventions**: anything done to a running game from outside the agent (a harness tool call while debugging, a screen closed by hand, a restart to deploy a fix) goes in `interventions.jsonl` with its turn and effect.
- Before the agent starts, `--prepare` loads the start save and checks that every unit has full moves, so a stray click during the load can't cost the agent a turn (see [docs/setup.md](docs/setup.md)).

Results land in [`results/`](results/); `tools/report.py` builds one page comparing all games. Details are in [`docs/plan.md`](docs/plan.md).

## Layout

- `vendor/civ6-mcp` - the MCP server (git submodule, pinned)
- `windows/` - PowerShell for the Windows game PC: fastest settings, scheduled tasks that launch the game, click, take screenshots and run jobs inside the desktop session, the long-lived civ6-mcp HTTP server (`civ_mcp_http.py`), the archive's sync and per-turn capture, and the war room browser on the second screen
- `tools/run_game.py` - run one game with a Claude Code agent across sessions and accounts until it ends
- `tools/archive.py` - keep the full record of a running game (see above)
- `tools/timeline.py` - join a run's transcripts and civ6-mcp records into a per-turn timeline
- `tools/results.py` and `tools/report.py` - copy a finished game's public files into `results/`, and build one HTML page comparing the games (cost, pace, tech lead, standings)
- `tools/warroom/` and `warroom/` - the live war room page: map, standings, each agent's latest moves, thoughts and API cost
- `remote/` - run PowerShell on the game PC over SSH, in session 0 (`zps.sh`) or in the desktop session (`zexec.sh`), copy files, and keep the SSH tunnel to the MCP server (`tunnel.sh`). `CIV_HOST` defaults to `zenbook`.
- `tools/tuner_exec.py` - run Lua in any named Civ 6 Lua state over FireTuner (only while no MCP server holds the connection)
- `tools/mcp_call.py` - call civ6-mcp tools directly, for smoke tests and timing
- `lua/` - front-end Lua (accept the copyright screen, start a new game or load a save from the main menu, list DLC ownership) and the base-game compatibility prelude
- `prompts/` - the notes added to every agent's system prompt
- `docs/setup.md` - how the rig is put together and what we learned

## Credits

- [lmwilki/civ6-mcp](https://github.com/lmwilki/civ6-mcp) and the CivBench paper, by Andrews, Wilkinson et al.
- [Johnor12/civ6-mcp](https://github.com/Johnor12/civ6-mcp): the MCP Bridge UI mod that makes hotseat play possible
- [SalukiSwift/civ6-deity](https://github.com/SalukiSwift/civ6-deity): scripted new-game setup from the main menu

## License

MIT. See [LICENSE](LICENSE).
