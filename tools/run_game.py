"""Run one Civ 6 game with a Claude Code agent, across sessions and accounts, until the game ends.

The agent is Claude Code in headless mode with only the civ6-mcp tools: no built-in tools (no shell, files
or web), no CLAUDE.md, memory, hooks, skills or other MCP servers. Its system prompt is the CivBench
playbook (track "standard") or CivBench's minimal baseline (track "baseline"), plus our base-game, speed
(batch tools), autonomy and optional victory-goal notes.

A -p session ends whenever the model stops calling tools. The runner then resumes the same session with
"Continue". When an account hits a usage limit, the session moves to a fresh account and continues there.
It stops when civ6-mcp reports the game over, the turn limit is reached, or a STOP file
appears in the run directory.

Writes, in --runtime-dir/<game-id>/ (private: it holds account names and transcript paths):
  game.json       war room manifest (title, game key, run id, agents and their transcripts)
  sessions.json   one row per session: account, session id, times, why it ended, usage
  events/NN.jsonl the raw stream-json events of each session (thinking, messages, tool calls, results)
  archive/        everything else, kept in sync by tools/archive.py while the game runs

--prepare first points civ6-mcp at this game: it writes the server's env file on the game PC (run id pinned
to the game id, so the diary survives server restarts; run_lua off), deletes old civ6-mcp autosaves,
restarts the server and, with --load-save, loads that save.

    python3 tools/run_game.py --game-id g1-standard --track standard \\
        --game-key sumeria_20261106 --civ "Sumeria (Gilgamesh)" --turn-limit 330 --prepare --load-save AutoSave_0001
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROMPTS = REPO / "prompts"
VENDOR = REPO / "vendor" / "civ6-mcp"

GOALS = {
    "science": "a Science victory: complete the space projects before anyone else",
    "domination": "a Domination victory: hold every other civilization's original capital",
    "culture": "a Culture victory: attract more visiting tourists than any civilization has domestic tourists",
    "religious": "a Religious victory: make your religion the majority in every civilization",
}
LIMIT_TEXT = re.compile(r"hit your .*limit|usage limit|limit reached|out of (extra )?usage", re.I)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def baseline_prompt() -> str:
    """CivBench's minimal open-track prompt, read from the vendored evals/prompts.py without importing it."""
    src = (VENDOR / "evals" / "prompts.py").read_text()
    m = re.search(r'BASELINE_SYSTEM_PROMPT = """\\\n(.*?)"""', src, re.S)
    if not m:
        raise SystemExit("run_game: BASELINE_SYSTEM_PROMPT not found in vendor/civ6-mcp/evals/prompts.py")
    return m.group(1).replace("\\\n", "")


def system_prompt(track: str, goal: str | None) -> str:
    parts = [(VENDOR / "AGENTS.md").read_text() if track == "standard" else baseline_prompt()]
    parts.append((PROMPTS / "base-game.md").read_text())
    parts.append((PROMPTS / "speed.md").read_text())
    if goal:
        parts.append(
            f"## Your goal\n\nWin by {GOALS[goal]}. Every victory type stays enabled for every civilization, "
            "but steer the whole game toward this one."
        )
    parts.append((PROMPTS / "autonomy.md").read_text())
    return "\n\n".join(p.strip() for p in parts) + "\n"


def kickoff_prompt(a: argparse.Namespace) -> str:
    objective = f"Win the game, ideally by {GOALS[a.goal]}." if a.goal else "Win the game. Any victory type counts."
    return (
        f"## Game: {a.title}\n\n"
        f"**Civilization:** {a.civ}\n**Difficulty:** {a.difficulty}\n**Map:** {a.map}\n"
        f"**Game speed:** {a.speed}\n**Turn limit:** {a.turn_limit}\n\n"
        f"### Objective\n\n{objective}\n\n"
        "### Getting started\n\nThe game is loaded and waiting on your first turn. Call `get_game_overview` "
        "to orient yourself and begin playing.\n\n"
        "### Saves\n\nThe game autosaves every turn as `0_MCP_NNNN`. To recover from a crash or a bad state, "
        'call `list_saves` and `load_game_save("0_MCP_NNNN")` with the most recent one.\n'
    )


RESUME_PROMPT = (
    "You are resuming this game in a new session; your earlier context is gone. Call `get_diary(last_n=5)` "
    "to recover your plans, then `get_game_overview`, and keep playing."
)
CONTINUE_PROMPT = "Continue"


def usage_limit(events: list[dict]) -> tuple[str, float | None] | None:
    """(limit kind, reset unix time or None) when a usage limit stopped the session.
    Same checks as the Kenso subagents runner: a rejected rate_limit_event, or the limit text in the result."""
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    if result and not result.get("is_error"):
        return None
    for e in events:
        info = e.get("rate_limit_info") or {}
        if e.get("type") == "rate_limit_event" and str(info.get("status")).lower() == "rejected":
            reset = info.get("resetsAt")
            if isinstance(reset, (int, float)) and reset > 1e11:
                reset /= 1000
            return str(info.get("rateLimitType") or "unknown"), reset
    if LIMIT_TEXT.search(str(result.get("result") or "")):
        return "unknown", None
    return None


def transcript_path(config_dir: Path, session_id: str) -> str | None:
    hit = next((config_dir / "projects").glob(f"*/{session_id}.jsonl"), None)
    return str(hit) if hit else None


def heartbeat(a: argparse.Namespace) -> dict:
    """civ6-mcp's ~/.civ6-mcp/heartbeat.json on the game PC: {"phase": "playing" | "finished", "turn": N, ...}."""
    ps = "Get-Content (Join-Path $env:USERPROFILE '.civ6-mcp\\heartbeat.json') -Raw"
    try:
        out = subprocess.run([str(REPO / "remote" / "zps.sh"), "-c", ps], capture_output=True, text=True, timeout=60).stdout
        return json.loads(out[out.index("{"): out.rindex("}") + 1])
    except Exception:
        return {}


class Run:
    def __init__(self, a: argparse.Namespace):
        self.a = a
        self.dir = Path(a.runtime_dir).expanduser() / a.game_id
        (self.dir / "events").mkdir(parents=True, exist_ok=True)
        (self.dir / "work").mkdir(exist_ok=True)
        self.sessions_file = self.dir / "sessions.json"
        self.sessions: list[dict] = json.loads(self.sessions_file.read_text()) if self.sessions_file.exists() else []
        self.limited: dict[str, float] = {}
        self.held = None
        self.fleet = None if a.accounts else load_fleet()

    def write_setup(self) -> None:
        a = self.a
        (self.dir / "system.md").write_text(system_prompt(a.track, a.goal))
        (self.dir / "mcp.json").write_text(json.dumps({"mcpServers": {"civ6": {"type": "http", "url": a.mcp_url}}}, indent=2))
        (self.dir / "settings.json").write_text(json.dumps({"disableAllHooks": True}, indent=2))
        self.write_manifest()

    def write_manifest(self) -> None:
        a = self.a
        transcripts = [s["transcript"] for s in self.sessions if s.get("transcript")]
        manifest = {
            # game_key carries the run id: civ6-mcp names its files {kind}_{civ}_{seed}_{run id}, and the war room
            # and the archive follow only the files of this key, not earlier runs on the same map.
            "title": a.title, "game_id": a.game_id, "game_key": f"{a.game_key}_{a.run_id}", "run_id": a.run_id,
            "civ6mcp_dir": a.civ6mcp_dir, "track": a.track, "goal": a.goal, "effort": a.effort,
            "civ": a.civ, "difficulty": a.difficulty, "map": a.map, "speed": a.speed, "turn_limit": a.turn_limit,
            "started_at": self.sessions[0]["started"] if self.sessions else None,
            "agents": [{"name": a.agent_name, "pid": 0, "goal": a.goal, "model": a.model, "transcripts": transcripts}],
        }
        tmp = self.dir / "game.json.tmp"
        tmp.write_text(json.dumps(manifest, indent=2))
        tmp.replace(self.dir / "game.json")

    def save_sessions(self) -> None:
        tmp = self.sessions_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.sessions, indent=2))
        tmp.replace(self.sessions_file)

    # --- Accounts -------------------------------------------------------------------------------------
    # By default the game claims accounts the way every Kenso subagent does (ken-internal subagents runner):
    # the least-loaded signed-in account of --use-case in the Claude Accounts sheet, reserved so no other
    # session runs on it, counted in "Subagents Now", and marked limited when it hits a usage limit. The game
    # keeps one account until it hits a limit, then moves the session to a fresh account and continues it
    # there with its context intact. --accounts replaces the sheet with a fixed list.

    def claim(self) -> str:
        if self.a.accounts:
            while True:
                for acct in self.a.accounts:
                    if self.limited.get(acct, 0) <= time.time():
                        return acct
                wake = min(self.limited.values()) + 60
                print(f"run_game: every account is limited, sleeping until {time.ctime(wake)}", file=sys.stderr)
                time.sleep(max(60, wake - time.time()))
        row, self.held = self.fleet.claim(self.a.use_case, set())
        return row["email"]

    def drop(self, acct: str, until: float) -> None:
        """acct hit a usage limit: give it back and keep others off it until it resets."""
        if self.a.accounts:
            self.limited[acct] = until
            return
        with self.fleet.sheet_lock():
            self.fleet.mark_limited(acct, until)
        self.release(acct)

    def release(self, acct: str | None) -> None:
        if self.a.accounts or not acct or self.held is None:
            return
        try:
            self.fleet.release(acct)
        finally:
            self.held.close()
            self.held = None

    def claude_cmd(self, acct: str, prompt: str, resume: str | None) -> list[str]:
        a = self.a
        cmd = shlex.split(a.claude_cmd.format(account=acct)) + [
            "-p", prompt, "--model", a.model, "--effort", a.effort,
            # Headless sessions omit thinking text unless asked: summaries go into the stream and the transcript.
            "--thinking-display", "summarized",
            "--system-prompt-file", str(self.dir / "system.md"),
            "--mcp-config", str(self.dir / "mcp.json"), "--strict-mcp-config",
            "--tools", "", "--allowedTools", "mcp__civ6", "--disable-slash-commands",
            "--settings", str(self.dir / "settings.json"),
            "--output-format", "stream-json", "--verbose",
        ]
        if resume:
            cmd += ["--resume", resume]
        return cmd

    def run_session(self, acct: str, prompt: str, resume: str | None) -> dict:
        n = len(self.sessions) + 1
        row = {"n": n, "account": acct, "started": now(), "resumed_from": resume, "prompt": prompt[:200]}
        self.sessions.append(row)
        self.save_sessions()
        env = os.environ | {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
        config_dir = Path.home() / f".claude-{acct}"
        events: list[dict] = []
        with open(self.dir / "events" / f"{n:03d}.jsonl", "w") as log:
            p = subprocess.Popen(self.claude_cmd(acct, prompt, resume), cwd=self.dir / "work", env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                log.write(line)
                log.flush()
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                events.append(e)
                if e.get("session_id") and not row.get("session_id"):
                    row["session_id"] = e["session_id"]
                    self.save_sessions()
                if row.get("session_id") and not row.get("transcript"):
                    if tp := transcript_path(config_dir, row["session_id"]):
                        row["transcript"] = tp
                        self.save_sessions()
                        self.write_manifest()
            code = p.wait()
        result = next((e for e in reversed(events) if e.get("type") == "result"), {})
        row.update(ended=now(), exit_code=code, is_error=bool(result.get("is_error")),
                   num_turns=result.get("num_turns"), usage=result.get("usage"),
                   result=str(result.get("result") or "")[:500])
        if row.get("session_id") and not row.get("transcript"):
            row["transcript"] = transcript_path(config_dir, row["session_id"])
        if hit := usage_limit(events):
            kind, reset = hit
            row["limit"] = {"kind": kind, "resets": reset}
            self.limited[acct] = reset or time.time() + 3600
        self.save_sessions()
        self.write_manifest()
        return row

    def stop_reason(self) -> str | None:
        if (self.dir / "STOP").exists():
            return "STOP file"
        hb = heartbeat(self.a)
        if hb.get("phase") == "finished":
            return f"game over (heartbeat: {hb})"
        if int(hb.get("turn") or 0) >= self.a.turn_limit:
            return f"turn limit {self.a.turn_limit} reached"
        if len(self.sessions) >= self.a.max_sessions:
            return f"max sessions {self.a.max_sessions}"
        return None

    def prepare(self) -> None:
        """Point civ6-mcp at this game: env file, old autosaves gone, server restarted, save loaded."""
        a = self.a
        env = {
            "CIV_MCP_DISABLE_LUA": "1", "CIV_MCP_AGENT_MODEL": a.model, "CIV_MCP_RUN_ID": a.run_id,
            "CIV_MCP_METADATA": json.dumps({"game_id": a.game_id, "track": a.track, "goal": a.goal, "effort": a.effort}),
        }
        body = json.dumps(env).replace("'", "''")
        write = f"Set-Content -Path (Join-Path $env:USERPROFILE 'civ6-bench\\mcp-env.json') -Value '{body}' -Encoding UTF8; 'env written'"
        print(subprocess.run([str(REPO / "remote" / "zps.sh"), "-c", write], capture_output=True, text=True).stdout.strip(), file=sys.stderr)
        clean = ("$d = Join-Path ([Environment]::GetFolderPath('MyDocuments')) \"My Games\\Sid Meier's Civilization VI\\Saves\\Single\"; "
                 "Get-ChildItem $d -Filter '0_MCP_*.Civ6Save' | Remove-Item -Force; 'old autosaves removed'")
        print(subprocess.run([str(REPO / "remote" / "zps.sh"), "-c", clean], capture_output=True, text=True).stdout.strip(), file=sys.stderr)
        out = subprocess.run([str(REPO / "remote" / "zexec.sh"), str(REPO / "windows" / "restart-mcp-http.ps1"), "120"],
                             capture_output=True, text=True).stdout
        print(f"run_game: {out.strip()}", file=sys.stderr)
        if a.load_save:
            self.load_clean(a.load_save)

    def mcp(self, tool: str, args: dict | None = None, timeout: int = 120) -> str:
        """One civ6-mcp tool call through tools/mcp_call.py; returns its printed result."""
        return subprocess.run(["uv", "run", "-q", "--with", "mcp==1.26.0", "python", str(REPO / "tools" / "mcp_call.py"),
                               "--url", self.a.mcp_url, "--chars", "4000", tool, json.dumps(args or {})],
                              capture_output=True, text=True, timeout=timeout, cwd=REPO).stdout

    def load_clean(self, save: str, tries: int = 3) -> None:
        """Load a turn-start save and check that every unit still has all its moves before the agent starts.

        civ6-mcp dismisses the leader screen by clicking CONTINUE GAME low on the screen. When the screen closes
        between mouse down and up, the click lands on the map and walks the selected unit (game 1's settler lost
        turn 1 this way). A turn-start save has every unit at full moves, so anything less means a stray click:
        load again.
        """
        for attempt in range(1, tries + 1):
            out = self.mcp("restart_and_load", {"save_name": save}, timeout=600)
            print(f"run_game: {out.strip()}", file=sys.stderr)
            units = ""
            for _ in range(12):  # the FireTuner port can take a few seconds to open after the load
                time.sleep(5)
                units = self.mcp("get_units")
                if re.search(r"\d+ units:", units):
                    break
            moves = re.findall(r"^\s*(.+?) at \((\d+,\d+)\).*?moves ([\d.]+)/([\d.]+)", units, re.M)
            spent = [f"{u} at ({xy}) {m}/{mx}" for u, xy, m, mx in moves if float(m) < float(mx)]
            if moves and not spent:
                print(f"run_game: start check passed: {len(moves)} units at full moves", file=sys.stderr)
                return
            why = f"units already moved: {'; '.join(spent)}" if spent else f"no unit list: {units.strip()[-300:]}"
            print(f"run_game: start check failed (load {attempt}/{tries}): {why}", file=sys.stderr)
        raise SystemExit(f"run_game: {save} did not load cleanly after {tries} tries; not starting the agent")

    def start_archive(self) -> subprocess.Popen:
        log = open(self.dir / "archive.stderr", "a")
        return subprocess.Popen([sys.executable, str(REPO / "tools" / "archive.py"), "--run-dir", str(self.dir)],
                                stdout=log, stderr=log)

    def start_warroom(self) -> subprocess.Popen | None:
        if not self.a.warroom:
            return None
        log = open(self.dir / "warroom.stderr", "a")
        return subprocess.Popen([sys.executable, str(REPO / "tools" / "warroom" / "collect.py"), "--manifest",
                                 str(self.dir / "game.json"), "--out", str(Path(self.a.warroom).expanduser()), "--publish"],
                                stdout=log, stderr=log)

    def play(self) -> None:
        self.write_setup()
        helpers = [self.start_archive(), self.start_warroom()]
        try:
            self.play_sessions()
        finally:
            for h in helpers:
                if h:
                    h.terminate()
            subprocess.run([sys.executable, str(REPO / "tools" / "archive.py"), "--run-dir", str(self.dir), "--once"])

    def play_sessions(self) -> None:
        acct = self.claim()
        try:
            while not (why := self.stop_reason()):
                last = self.sessions[-1] if self.sessions else None
                if last is None:
                    prompt, resume = kickoff_prompt(self.a), None
                elif last.get("session_id") and (src := transcript_file(last)):
                    if last["account"] != acct:
                        move_session(src, acct)  # same session, new account: the agent keeps its context
                    prompt, resume = CONTINUE_PROMPT, last["session_id"]
                else:
                    prompt, resume = RESUME_PROMPT, None
                print(f"run_game: session {len(self.sessions) + 1}" + (f", resuming {resume}" if resume else ", new"), file=sys.stderr)
                slot = None
                if not self.a.accounts:
                    slot = self.fleet.take_slot()
                    self.fleet.stagger()
                try:
                    row = self.run_session(acct, prompt, resume)
                finally:
                    if slot:
                        slot.close()
                if row.get("limit"):
                    self.drop(acct, row["limit"]["resets"] or time.time() + 3600)
                    acct = self.claim()
                elif row.get("exit_code") and not row.get("session_id"):
                    raise SystemExit(f"run_game: claude failed to start (exit {row['exit_code']}): {row.get('result')}")
                elif row.get("is_error") and seconds(row) < 120:
                    time.sleep(60)  # a quick failure (API overload, network): don't spin
        finally:
            self.release(acct)
        print(f"run_game: stopped: {why}", file=sys.stderr)


def seconds(row: dict) -> float:
    try:
        return (datetime.fromisoformat(row["ended"]) - datetime.fromisoformat(row["started"])).total_seconds()
    except (KeyError, ValueError):
        return 0


def transcript_file(row: dict) -> Path | None:
    p = Path(row["transcript"]) if row.get("transcript") else None
    return p if p and p.exists() else None


def move_session(src: Path, acct: str) -> None:
    """Copy a session transcript into acct's config dir so --resume finds it there."""
    dest = Path.home() / f".claude-{acct}" / "projects" / src.parent.name
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest / src.name)


def load_fleet():
    """The newest ken-internal subagents runner, for its account claims, slots and limit tracking."""
    base = Path.home() / ".claude" / "plugins" / "cache" / "ken-plugins" / "ken-internal"
    found = sorted(base.glob("*/skills/subagents/scripts/run_on_account.py"),
                   key=lambda p: [int(x) for x in re.findall(r"\d+", p.parts[-5])])
    if not found:
        raise SystemExit(f"run_game: no ken-internal subagents runner under {base}; pass --accounts")
    sys.path.insert(0, str(found[-1].parent))
    import run_on_account
    return run_on_account


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-id", required=True)
    ap.add_argument("--track", choices=["standard", "baseline"], required=True)
    ap.add_argument("--goal", choices=sorted(GOALS))
    ap.add_argument("--accounts", type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
                    help="fixed comma-separated account list instead of claiming from the Claude Accounts sheet")
    ap.add_argument("--use-case", default="Development", help="Claude Accounts sheet use case to claim from")
    ap.add_argument("--game-key", required=True, help="civ6-mcp file key, {civ}_{seed}, e.g. sumeria_20261106")
    ap.add_argument("--run-id", help="civ6-mcp run id for this game's files (default: the game id; no underscores)")
    ap.add_argument("--prepare", action="store_true", help="set up civ6-mcp for this game first (see above)")
    ap.add_argument("--load-save", help="with --prepare: load this save, e.g. AutoSave_0001")
    ap.add_argument("--title", default="Opus 5.5 vs the built-in AI")
    ap.add_argument("--agent-name", default="Opus 5.5")
    ap.add_argument("--civ", default="Sumeria (Gilgamesh)")
    ap.add_argument("--difficulty", default="Prince")
    ap.add_argument("--map", default="Pangaea, standard size")
    ap.add_argument("--speed", default="Quick")
    ap.add_argument("--turn-limit", type=int, default=330)
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--mcp-url", default="http://127.0.0.1:18771/mcp")
    ap.add_argument("--civ6mcp-dir", default="%USERPROFILE%\\.civ6-mcp", help="where civ6-mcp writes its JSONL on the game PC")
    ap.add_argument("--claude-cmd", default="claude-acct {account}", help="command that runs Claude Code as {account}")
    ap.add_argument("--runtime-dir", default="~/.civ6-bench/runs")
    ap.add_argument("--warroom", help="also run the war room collector, publishing the page to this folder")
    ap.add_argument("--max-sessions", type=int, default=400)
    ap.add_argument("--print-prompts", action="store_true", help="print the system and kickoff prompts and exit")
    a = ap.parse_args()
    a.run_id = (a.run_id or a.game_id).replace("_", "-")
    if a.print_prompts:
        print(system_prompt(a.track, a.goal))
        print("=" * 80)
        print(kickoff_prompt(a))
        return
    run = Run(a)
    if a.prepare:
        run.prepare()
    run.play()


if __name__ == "__main__":
    main()
