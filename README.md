# civ6-benchmark

How well does Claude Opus 5.5 play Sid Meier's Civilization VI?

This repo holds the setup, harness glue and results for running LLM agents in real Civ 6 games. It was inspired by Dwarkesh Patel's [Blood on the Clocktower benchmark](https://www.dwarkesh.com/p/clocktower). The game itself is driven by [lmwilki/civ6-mcp](https://github.com/lmwilki/civ6-mcp) (MIT), an MCP server that talks to Civ 6 through its built-in FireTuner debug port. That is the same harness the CivBench paper used ([arXiv 2609.02459](https://arxiv.org/abs/2609.02459)).

## Experiments

| # | Setup | Status |
|---|---|---|
| 1 | Opus 5.5 (high effort) vs the built-in AI on Pangaea, standard size, Quick, Prince, **with** the civ6-mcp playbook | setting up |
| 2 | Same map, **rules only**, no strategy playbook | planned |
| 3 | Assigned victory goal (Science, then Domination), Online speed. Every victory type stays on, and any win counts; we also record whether it matched the goal | planned |
| 4 | Opus vs Opus on a standard 8-civ map, Online speed: (A) 1 Opus + 7 AI vs (B) 4 Opus + 4 AI, same seed and civs | planned |

All games use the **base game** ruleset (no Rise and Fall or Gathering Storm), so there's no diplomatic victory, and results don't compare directly with CivBench, which used Gathering Storm.

Every game reports API-equivalent cost: input, output, cache-read and cache-write tokens, priced at list API rates, even though runs use Claude subscriptions.

Results land in [`results/`](results/). Details are in [`docs/plan.md`](docs/plan.md).

## Layout

- `vendor/civ6-mcp` - the MCP server (git submodule, pinned)
- `windows/` - PowerShell for the Windows game PC: fastest graphics settings, scheduled tasks that launch the game, click and take screenshots inside the desktop session
- `remote/` - run PowerShell on the game PC over SSH, and copy files to and from it (`CIV_HOST`, default `zenbook`)
- `tools/tuner_exec.py` - run Lua in any named Civ 6 Lua state over FireTuner
- `lua/` - front-end Lua: accept the copyright screen, load a save from the main menu, list DLC ownership
- `docs/setup.md` - how the rig is put together and what we learned

## Credits

- [lmwilki/civ6-mcp](https://github.com/lmwilki/civ6-mcp) and the CivBench paper, by Andrews, Wilkinson et al.
- [Johnor12/civ6-mcp](https://github.com/Johnor12/civ6-mcp): the MCP Bridge UI mod that makes hotseat play possible
- [SalukiSwift/civ6-deity](https://github.com/SalukiSwift/civ6-deity): scripted new-game setup from the main menu

## License

MIT. See [LICENSE](LICENSE).
