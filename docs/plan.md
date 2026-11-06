# Experiment plan

## 1-2. Opus 5.5 vs the built-in AI (CivBench-comparable)

- Scenario: CivBench "Ground Control", loaded from civ6-mcp `evals/saves/0A_GROUND_CONTROL.Civ6Save` (Babylon, Pangaea, standard size, Quick, Prince).
- Agent: Claude Code with Opus 5.5 at high effort and civ6-mcp's 76 tools. Game 1 uses the stock playbook (`CLAUDE.md` / `AGENTS.md`). Game 2 gets only the rules and tool reference.
- Played to a result, or to the turn limit (330 on Quick).
- Compared with CivBench's published Opus 4.6 runs: 2 wins in 8 games on Prince.

## 3. Assigned-victory games

- The agent's prompt names one victory type: science, culture, domination, religious or diplomatic (diplomatic needs Gathering Storm).
- All victory types stay enabled for every civ. The game counts as a success only if the agent wins by its assigned type. A win of any other type, or any loss, counts as a failure.
- Metrics: success, the turn of the win, how close the assigned victory got (the matching `get_victory_progress` numbers), and cost.

## 4. Opus vs Opus

- Same map and civs under two conditions: (A) one Opus civ against built-in AI civs, (B) every major civ played by its own Opus agent.
- Hotseat runs every seat through the MCP Bridge UI mod (Johnor12/civ6-mcp), because FireTuner is off in hotseat. Each civ's agent keeps its own session and diary and sees only what its civ can see.
- Optional: a private message channel between leaders, for alliances and betrayals.

## Accounting

- Runs use Claude subscriptions, never API keys. One game is one long Claude Code session per civ. When an account hits a limit, the next account resumes from the per-turn save and the diary.
- Each session's usage (input, output, cache read, cache write) is logged per turn and priced at list API rates for the model. The report gives tokens and dollars per game and per turn.
