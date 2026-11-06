"""Archive everything about one game run while it plays, so the run can be replayed and analyzed later.

tools/run_game.py starts this next to the agent and runs a final pass when the game stops. It reads the run
directory's game.json (game key, run id) and sessions.json (transcripts) and keeps <run dir>/archive/ in sync:

  civ6mcp/       civ6-mcp's own records for this game and run, mirrored from the game PC:
                   log_*.jsonl       every tool call: params, the full result, duration, turn
                   diary_*.jsonl     per turn, a row per civ (score, yields, techs, military, religion, ...)
                                     and the agent's five reflections (tactical, strategic, tooling, planning,
                                     hypothesis)
                   diary_*_cities.jsonl, mapturns_*.jsonl, mapstatic_*.json, spatial_*.jsonl, heartbeat.json
  transcripts/   each Claude Code session transcript: the agent's thinking, messages, tool calls and results
  shots/         a screenshot of both screens at the start of each turn (T0042.jpg), taken on the game PC by a
                 loop that polls civ6-mcp's heartbeat every 2 s
  saves/         every civ6-mcp autosave (0_MCP_0042.Civ6Save), so any turn can be reloaded
  timeline.jsonl, turns.jsonl, timeline.md
                 the transcripts and civ6-mcp's log joined per turn (tools/timeline.py), rebuilt after each sync
  archive.log

The game PC side is windows/archive-sync.ps1 (incremental file sync, one SSH call per cycle) and
windows/archive-turn.ps1 (the Civ6Archive task: screenshot and saves, started on each new turn).

    python3 tools/archive.py --run-dir ~/.civ6-bench/runs/g1-standard [--interval 10] [--once]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import timeline  # noqa: E402

HOST = os.environ.get("CIV_HOST", "zenbook")
# The spec goes on stdin: with hundreds of archived files it outgrows a Windows command line.
_RUN_SYNC = "& (Join-Path $env:USERPROFILE 'civ6-bench\\archive-sync.ps1')"
SYNC_CMD = "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand " + base64.b64encode(
    _RUN_SYNC.encode("utf-16-le")).decode()
BENCH = "%USERPROFILE%\\civ6-bench"
BUDGET = 6_000_000  # bytes per SSH call; the rest comes in the next call


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def tail_hash(path: Path, size: int) -> str:
    with open(path, "rb") as f:
        start = max(0, size - 4096)
        f.seek(start)
        return hashlib.sha1(f.read(size - start)).hexdigest()


class Archiver:
    def __init__(self, run_dir: Path):
        self.run = run_dir
        self.out = run_dir / "archive"
        for sub in ("civ6mcp", "transcripts", "shots", "saves"):
            (self.out / sub).mkdir(parents=True, exist_ok=True)
        self.state_file = self.out / "state.json"
        self.state = json.loads(self.state_file.read_text()) if self.state_file.exists() else {}
        self.state.setdefault("since", int(time.time()) - 60)

    def log(self, msg: str) -> None:
        with open(self.out / "archive.log", "a") as f:
            f.write(f"{stamp()} {msg}\n")

    def save_state(self) -> None:
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=2))
        tmp.replace(self.state_file)

    def manifest(self) -> dict:
        return json.loads((self.run / "game.json").read_text())

    def have(self) -> tuple[dict, dict]:
        """What the archive holds: size and tail hash per file, and for shots and saves a name watermark.

        Shots (T0042.jpg) and saves (0_MCP_0042) come one per turn, so only the newest of each is listed by size
        (it may still have been copying) and the game PC skips names that sort before it. That keeps the spec,
        which goes on stdin, a few KB for the whole game: Windows OpenSSH stalls on stdin past about 8 KB.
        """
        have, after = {}, {}
        for key in ("civ6mcp", "shots", "saves"):
            files = sorted(p for p in (self.out / key).iterdir() if p.is_file())
            if key in ("shots", "saves") and files:
                after[key] = files[-1].name
                files = files[-1:]
            for p in files:
                size = p.stat().st_size
                have[f"{key}/{p.name}"] = {"size": size, "tail": tail_hash(p, size) if size else ""}
        return have, after

    def spec(self, trigger: dict | None) -> dict:
        m = self.manifest()
        game_dir = f"{BENCH}\\archive\\{m['game_id']}"
        have, after = self.have()
        spec = {
            "roots": [
                {"key": "civ6mcp", "dir": "%USERPROFILE%\\.civ6-mcp",
                 "match": [f"*_{m['game_key']}*", "heartbeat.json"]},
                {"key": "shots", "dir": f"{game_dir}\\shots", "match": ["*.jpg"], "after": after.get("shots")},
                {"key": "saves", "dir": f"{game_dir}\\saves", "match": ["*.Civ6Save"], "after": after.get("saves")},
            ],
            "have": have,
            "budget": BUDGET,
        }
        if trigger:
            spec["trigger"] = trigger
        return spec

    def remote(self, spec: dict) -> tuple[int, bool]:
        """One sync call. Returns (files updated, whether more is waiting)."""
        b64 = base64.b64encode(json.dumps(spec).encode()).decode()
        out = subprocess.run(["ssh", "-o", "BatchMode=yes", HOST, SYNC_CMD], input=b64, capture_output=True,
                             text=True, timeout=300).stdout
        n, more = 0, False
        for line in out.splitlines():
            if line.strip() == "MORE":
                more = True
            if not line.startswith("F\t"):
                continue
            _, name, size, offset, data = (line.split("\t") + [""])[:5]
            key, fname = name.split("/", 1)
            path = self.out / key / fname
            offset = int(offset)
            mode = "r+b" if path.exists() else "wb"
            with open(path, mode) as f:
                f.seek(offset)
                f.write(base64.b64decode(data))
                f.truncate()
            n += 1
        return n, more

    def heartbeat_turn(self) -> int:
        try:
            return int(json.loads((self.out / "civ6mcp" / "heartbeat.json").read_text()).get("turn") or 0)
        except Exception:
            return 0

    def copy_transcripts(self) -> int:
        sessions_file = self.run / "sessions.json"
        if not sessions_file.exists():
            return 0
        n, seen = 0, set()
        for s in json.loads(sessions_file.read_text()):
            src = Path(s["transcript"]) if s.get("transcript") else None
            if not src or not src.exists() or src in seen:
                continue  # a resumed session keeps writing the transcript it started: one copy, named by its first run
            seen.add(src)
            dest = self.out / "transcripts" / f"{s['n']:03d}-{s['session_id']}.jsonl"
            if not dest.exists() or dest.stat().st_size != src.stat().st_size:
                shutil.copyfile(src, dest)
                n += 1
        return n

    def cycle(self, capture: bool = True) -> None:
        # Every sync (re)starts the per-turn capture loop on the game PC; a running loop ignores the start.
        trigger = {"game": self.manifest()["game_id"], "since": self.state["since"]} if capture else None
        total, more, calls = 0, True, 0
        while more and calls < 20:
            n, more = self.remote(self.spec(trigger if calls == 0 else None))
            total += n
            calls += 1
        t = self.copy_transcripts()
        if total or t:
            self.log(f"turn {self.heartbeat_turn()}: {total} file updates, {t} transcripts")
        if total or t or not (self.out / "turns.jsonl").exists():
            timeline.build(self.run)  # timeline.jsonl, turns.jsonl, timeline.md


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True, type=lambda s: Path(s).expanduser())
    ap.add_argument("--interval", type=float, default=10)
    ap.add_argument("--once", action="store_true", help="one pass, then exit (run_game.py runs this at the end)")
    ap.add_argument("--parent-pid", type=int, default=os.getppid(),
                    help="stop after a last pass once this process (the game runner) has exited")
    a = ap.parse_args()
    arch = Archiver(a.run_dir)
    while True:
        last = a.once or not alive(a.parent_pid)
        try:
            arch.cycle(capture=not last)
        except Exception as e:  # keep archiving through SSH drops and laptop sleeps
            arch.log(f"cycle failed: {e!r}")
            print(f"archive: cycle failed: {e!r}", file=sys.stderr)
        if last:
            return
        time.sleep(a.interval)


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return pid > 1
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


if __name__ == "__main__":
    main()
