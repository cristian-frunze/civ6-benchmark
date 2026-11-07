"""Watch a running hotseat game and reload the last seat's turn when the AI civs' turn hangs after it.

    python3 tools/hotseat_doctor.py --game-id h1-four-opus [--hang-minutes 20] [--max-reloads 2]

In game h1, after the last Opus seat ended turn 53, the AI civs' turn never finished: the game sat on the turn-change
screen's "please wait" state for 49 minutes, with no Lua error and no pending diplomacy, and tools/run_hotseat.py waits
for the next seat's turn forever. Reloading the save made at the start of that seat's turn (load_hotseat_save) fixed
it: the seat replayed its turn (run_hotseat.py's retry) and the AI civs then finished in seconds.

This does that by itself. Every 30 s it reads the run's files; when no seat is playing (every "turn N, seat" line the
runner printed has its row in turns.jsonl) and the last row ended more than --hang-minutes ago, it asks the server
once (hotseat_status). If the local player's turn is not active, it reloads the newest hotseat save, which end_turn made
at the start of the hung seat's turn, and appends the reload to the run's interventions.jsonl. It stops when the runner
does, or after --max-reloads reloads of the same turn (then the game needs a person).
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MCP = ["uv", "run", "--quiet", "--with", "mcp==1.26.0", "python", str(REPO / "tools" / "mcp_call.py"), "--chars", "4000"]
PLAYING = re.compile(r"run_hotseat: turn (\d+), (\S+) \(")


def mcp(tool: str, args: dict, timeout: int) -> str:
    out = subprocess.run(MCP + [tool, json.dumps(args)], capture_output=True, text=True, timeout=timeout)
    return out.stdout


def log(msg: str) -> None:
    print(time.strftime("%Y-%m-%dT%H:%M:%S ") + msg, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-id", required=True)
    ap.add_argument("--runtime-dir", default="~/.civ6-bench/runs")
    ap.add_argument("--hang-minutes", type=float, default=20)
    ap.add_argument("--max-reloads", type=int, default=2)
    a = ap.parse_args()
    runs = Path(a.runtime_dir).expanduser()
    run, runner_log = runs / a.game_id, runs / f"{a.game_id}.log"
    reloads: dict[int, int] = {}
    while True:
        time.sleep(30)
        text = runner_log.read_text(errors="replace") if runner_log.exists() else ""
        if "run_hotseat: stopped:" in text:
            log("runner stopped; done")
            return
        if subprocess.run(["pgrep", "-f", f"run_hotseat[.]py.*--game-id {a.game_id}"], capture_output=True).returncode:
            log("runner process gone; done")
            return
        rows = [json.loads(ln) for ln in open(run / "turns.jsonl")] if (run / "turns.jsonl").exists() else []
        if not rows:
            continue
        started = len(PLAYING.findall(text))
        if started > len(rows):
            continue  # a seat is playing
        idle = time.time() - rows[-1]["end"]
        if idle < a.hang_minutes * 60:
            continue
        status = mcp("hotseat_status", {}, 120)
        if "turn active=False" not in status:
            continue  # a turn-change screen or a seat's turn: the runner handles it
        turn = rows[-1]["turn"]
        if reloads.get(turn, 0) >= a.max_reloads:
            log(f"the AI civs' turn after turn {turn} hung again after {a.max_reloads} reloads; stopping, needs a person")
            return
        saves = [ln.strip() for ln in mcp("list_saves", {}, 120).splitlines() if ln.startswith("  ")]
        newest = next((s for s in saves if "[autosave]" not in s), "")
        if f" {turn} " not in f" {newest} ":
            log(f"newest save {newest!r} is not from turn {turn}; stopping, needs a person")
            return
        log(f"AI turn after {rows[-1]['seat']}'s turn {turn} idle {idle / 60:.0f} min; reloading {newest!r}")
        out = mcp("load_hotseat_save", {"save_name": newest}, 700)
        ok = "Loaded hotseat save" in out
        log(out.strip().splitlines()[-1] if out.strip() else "no output")
        reloads[turn] = reloads.get(turn, 0) + 1
        with open(run / "interventions.jsonl", "a") as f:
            f.write(json.dumps({
                "ts": time.time(), "when": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "turn": turn,
                "who": "tools/hotseat_doctor.py (automatic)",
                "action": f"Reloaded the hotseat save {newest!r} (start of {rows[-1]['seat']}'s turn {turn})"
                          + ("" if ok else " - the load did not report success"),
                "why": f"The AI civs' turn after {rows[-1]['seat']} ended turn {turn} had not finished after "
                       f"{idle / 60:.0f} minutes. That seat's turn-{turn} orders are undone and it plays the turn again.",
                "game_state_changed": True}) + "\n")
        if not ok:
            log("load failed; stopping, needs a person")
            return


if __name__ == "__main__":
    sys.exit(main())
