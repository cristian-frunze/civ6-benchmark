# War room

A live page for watching a game: a god view of the map, the standings of every major civ, and one pane per Opus agent with its status, latest reasoning, diary reflections, recent tool calls, trends and cost. It is built for the Zenbook's bottom screen (2880x1800 at 200%, about 1440x900 CSS px) next to the game on the top screen. It fits 1 to 8 agents without scrolling and also works on a phone.

Plain HTML, CSS and JS with no build step and no CDN. Fonts are bundled in `fonts/` (Barlow Condensed, IBM Plex Mono and Newsreader, all SIL OFL 1.1, licenses alongside).

## How it fits together

```
game PC: civ6-mcp writes ~/.civ6-mcp/*.jsonl      dev server: Claude Code transcripts
        \                                          /
         tools/warroom/collect.py  (polls every few seconds)
                        |
             <out>/state.json  +  the page files (--publish)
                        |
             warroom/index.html polls state.json every 2 s
```

The collector reads the civ6-mcp files from the game PC with `remote/zps.sh`: one SSH call per cycle that lists the civ6-mcp folder and reads each tracked file from a byte offset, so the tool log (tens of MB per game) is never re-read whole. The first read of a big log starts at its last 2 MB. Files rewritten in place (civ6-mcp merges retried `end_turn` reflections into the diary) are noticed through the 256 bytes before each offset and re-read. On the game PC it only lists and reads files in the civ6-mcp folder.

## Run it

```bash
python3 tools/warroom/collect.py --manifest game.json --out ~/tailscale-share/civ6-warroom --publish
```

Then open the folder's URL in a browser. Any static file server works; `state.json` is fetched with a cache-busting query.

| Flag | Meaning |
|---|---|
| `--manifest FILE` | Game manifest (below). Re-read when it changes, so the runner can add a transcript mid-game. |
| `--out DIR` | Where `state.json` is written, atomically (temp file, then rename). |
| `--publish` | Also copy `index.html`, `style.css`, `app.js` and `fonts/` into `--out`. |
| `--local-dir DIR` | Read the civ6-mcp files from a local folder instead of the game PC (fixtures, tests). |
| `--interval N` | Seconds between cycles, default 3. A remote cycle takes about 4 s, so remote mode refreshes every 4-5 s. |
| `--once` | Write `state.json` once and exit. |

The game PC is `CIV_HOST` (default `zenbook`), as for the other `remote/` scripts. `WARROOM_REDACT` takes extra comma-separated words to strip from `state.json`. Prices come from `warroom/prices.json` (USD per million tokens, per model id). Without it the page shows tokens and no dollars.

Demo data: `tools/warroom/make_demo.py --out /tmp/warroom-demo [--real-transcript FILE.jsonl]` merges the four civ6-mcp fixture games into one 8-civ game with a synthetic map, tool log and transcripts, and writes `manifest-1.json`, `manifest-4.json` and `manifest-8.json`:

```bash
python3 tools/warroom/make_demo.py --out /tmp/warroom-demo
python3 tools/warroom/collect.py --manifest /tmp/warroom-demo/manifest-4.json \
    --local-dir /tmp/warroom-demo/civ6-mcp --out /tmp/warroom-out --publish --once
```

Tests: `python3 -m unittest tools/warroom/test_collect.py`.

## Manifest

Written by the game runner. It holds local paths, so it stays out of the repo and none of it except names, models and goals reaches `state.json`.

```json
{
  "title": "Game 1: Opus 5.5 vs AI, playbook",
  "game_key": "sumeria_-1838192045",
  "civ6mcp_dir": "C:\\Users\\<you>\\.civ6-mcp",
  "started_at": "2026-11-06T13:00:00Z",
  "demo": false,
  "agents": [
    {
      "name": "Opus 1",
      "pid": 0,
      "goal": null,
      "model": "claude-opus-5-5",
      "game_key": null,
      "transcripts": ["/home/<user>/.claude-<account>/projects/<project>/<session>.jsonl"]
    }
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `title` | no | Shown in the header. |
| `game_key` | no | `{civ}_{seed}` as in civ6-mcp file names (`diary_{civ}_{seed}_{run_id}.jsonl`). Every run id of that key is merged, so a game that resumed in a new MCP process still reads as one. Leave it out (or `"auto"`) to follow the newest diary or log in the folder. A key that matches no file also falls back to the newest game, with a warning on the page. |
| `civ6mcp_dir` | no | civ6-mcp folder on the game PC. Defaults to `%USERPROFILE%\.civ6-mcp`. Ignored with `--local-dir`. |
| `started_at` | no | ISO time or epoch seconds for the elapsed clock. Defaults to the first transcript line. |
| `demo` | no | `true` shows the "demo data" badge and freezes relative times at the snapshot. |
| `agents[].name` | yes | Pane title, also the tag in the standings. |
| `agents[].pid` | no | The agent's player id in the game. If missing, agents take the diary's `is_agent` players in order. |
| `agents[].goal` | no | Assigned victory goal, e.g. `"Science"`. `null` hides the chip. |
| `agents[].model` | no | Model id. Defaults to the model in the transcript. |
| `agents[].game_key` | no | Extra key for a hotseat seat whose MCP writes its own files. |
| `agents[].transcripts` | yes | Claude Code JSONL transcripts, oldest first. An agent that moves to a new session or account gets a new entry. Usage is summed across all of them plus their `subagents/*.jsonl`, counted once per API message id. |

## state.json

Written every cycle. Free text goes through a sanitizer that removes emails, file paths, IPs, tailnet host names and the local and game-PC user and host names. Times are Unix seconds.

```js
{
  "v": 1,
  "generated_at": 1793967479.9,
  "demo": false,
  "game": {
    "title": "Game 1: Opus 5.5 vs AI, playbook",
    "turn": 161,                    // max turn seen in the tool log, diary and heartbeat; null before the first
    "started_at": 1793962113.6,
    "ended_at": null,               // set once the game is over
    "mcp_phase": "playing",         // from civ6-mcp heartbeat.json: launching, loading, playing, finished, error
    "game_over": null               // or {turn, ts, winner_civ, winner_leader, victory_type, winner_pid, winner_agent}
  },
  "source": {"ok": true, "folder": true, "error": null, "files": 9, "note": null},   // collector health: game PC reachable, folder exists, tracked files, key fallback note
  "priced": true,                   // false when warroom/prices.json is missing
  "cost": {                         // all agents together
    "usd": 35.48,                   // null without prices
    "total": 76467556, "input": 4038, "output": 445830, "cache_read": 74562742,
    "cache_write_5m": 0, "cache_write_1h": 1454946,
    "unpriced_tokens": 0,           // tokens from models missing in prices.json
    "requests": 753                 // API responses counted
  },
  "civs": [                         // every major civ, sorted by score
    {
      "pid": 5, "civ": "Germany", "leader": "Frederick Barbarossa", "color": "#ff7eb6",
      "agent": null,                // index into agents[], or null for the built-in AI
      "rank": 1, "turn": 160,       // diary turn of these numbers
      "score": 300, "cities": 7, "pop": 44, "science": 82.0, "culture": 55.2,
      "gold_per_turn": 58, "faith_per_turn": 12, "military": 230, "techs": 40, "civics": 30, "era": "Industrial",
      "history": {"turn": [1, 10], "score": [15, 40], "science": [3.5, 9], "culture": [1.8, 6]}   // at most 120 points
    }
  ],
  "agents": [
    {
      "name": "Opus 1", "model": "claude-opus-5-5", "goal": "Science",
      "pid": 0, "civ": "Russia", "leader": "Peter", "color": "#ff5d47", "rank": 2,
      "status": "thinking",         // thinking | acting | waiting (an end_turn is running) | done | starting (no transcript lines yet)
      "stale": false,               // thinking or acting with no transcript activity for 15 minutes
      "last_activity": 1793967470.4,
      "first_ts": 1793962113.6,
      "sessions": 1,                // transcripts with activity
      "reasoning": {"kind": "thinking", "text": "...", "ts": 1793967470.1},   // latest thinking, else latest assistant text; null if none
      "earlier": [{"kind": "text", "text": "...", "ts": 1793967300.0}],      // up to 3 previous ones, newest first
      "reflections": {"turn": 160, "tactical": "...", "strategic": "...", "planning": "..."},   // latest diary row with reflections, or null
      "tools": [{"name": "unit_action", "args": "unit_id=5, action=move", "ts": 1793967470.4, "ok": null, "done_ts": null}],   // newest first, up to 10; ok null = still running
      "usage": {"usd": 3.69, "total": 3294013, "input": 66, "output": 85252, "cache_read": 3036770,
                "cache_write_5m": 0, "cache_write_1h": 171925, "unpriced_tokens": 0, "requests": 32}
    }
  ],
  "map": {                          // null until civ6-mcp's map capture has run
    "w": 84, "h": 54, "wrap_x": true, "rev": "3cd8e7864f",   // rev changes when owners or cities change
    "terrain":  "<base64>",         // one byte per plot, index y*w + x, y = 0 is the south edge. Civ 6 base-game
                                    // terrain index: 0-14 grass/plains/desert/tundra/snow (flat, hills, mountain), 15 coast, 16 ocean, 255 unknown
    "features": "<base64>",         // feature index + 1, 0 = none: 1 floodplains, 2 ice, 3 jungle, 4 forest, 5 oasis, 6 marsh, 7+ natural wonders
    "rivers":   "<base64>",         // 1 = river plot
    "owners":   "<base64>",         // owner player id + 1, 0 = unowned
    "cities": [{"x": 20, "y": 28, "pid": 0, "pop": 11, "name": "Moscow"}],
    "city_states": [{"pid": 8, "name": "Geneva", "type": "Scientific", "color": "#5f86b8"}]
  }
}
```

The map layout follows Civ 6: pointy-top hexes, odd rows shifted half a hex east, north up, wrapping east-west. The page puts the wrap seam on the column that cuts the least land and territory. The map is the latest `mapstatic_*.json` with every later `mapturns_*.jsonl` delta applied.

## What the page shows

- Header: title, turn, elapsed time, API-equivalent cost of all agents (hover for the token split), and whether the data is live. Warnings when the game PC is unreachable or civ6-mcp has written nothing yet. A banner when the game ends.
- Theater: terrain, territory per civ (agents brighter with a glowing border), cities sized by population, city-states in their type colors. Hover a city for details.
- Standings: score with a trend line, cities, science, culture, gold per turn and military for every major civ, agents tagged.
- Agent panes: civ, leader, goal, status, the latest reasoning (and earlier messages when there is room), the latest diary reflections, recent tool calls, score, science and culture trends, and tokens and dollars. Panes drop detail as they get smaller, so 8 agents still fit.
