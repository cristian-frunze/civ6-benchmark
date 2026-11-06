# Experiment plan

Ruleset: **base game** (no expansions). The CivBench saves need Gathering Storm and the New Frontier Pass civs, which this account doesn't own.

## 1-2. Opus 5.5 vs the built-in AI

- Our own fixed start: Pangaea, standard size, Quick, Prince, base-game civs, one pinned map seed for both games.
- Agent: Claude Code with Opus 5.5 at high effort and civ6-mcp's 76 tools. Game 1 uses the stock playbook (`CLAUDE.md` / `AGENTS.md`). Game 2 gets only the rules and tool reference.
- Played to a result, or to the turn limit (330 on Quick).
- CivBench's Opus 4.6 runs (2 wins in 8 on Prince, Gathering Storm) are context only, not a like-for-like comparison.

## 3. Assigned-victory games

- The agent's prompt names one victory goal. Science and Domination come first, Culture and Religious later. Online speed.
- All victory types stay enabled for every civ. Any win by the agent counts as a win. We also record whether the win matched the assigned goal.
- Metrics: success, the turn of the win, how close the assigned victory got (the matching `get_victory_progress` numbers), and cost.

## 4. Opus vs Opus

- Standard map, 8 civs, Online speed, with the same seed and civs in both conditions: (A) 1 Opus + 7 AI, (B) 4 Opus + 4 AI.
- Hotseat runs every seat through the MCP Bridge UI mod (Johnor12/civ6-mcp), because FireTuner is off in hotseat. Each civ's agent keeps its own session and diary and sees only what its civ can see.
- Optional: a private message channel between leaders, for alliances and betrayals.

## Accounting

- Runs use Claude subscriptions, never API keys. One game is one long Claude Code session per civ. When an account hits a limit, the next account resumes from the per-turn save and the diary.
- Each session's usage (input, output, cache read, cache write) is logged per turn and priced at list API rates for the model. The report gives tokens and dollars per game and per turn.
