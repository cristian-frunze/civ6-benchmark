"""Run one hotseat game: several Claude Code agents, one per hotseat seat, against civilizations the built-in AI runs.

Civ 6 turns FireTuner off in every multiplayer mode, hotseat included, so the agents use the hotseat fork of civ6-mcp
(Johnor12/civ6-mcp, MCP Bridge mod) behind windows/civ_mcp_hotseat.py. Start that server on the game PC and load the
game on a seat's turn-change screen first (lua/new-hotseat.lua makes a new one).

Each seat is one Claude Code session, resumed once per turn:
  coordinator: hotseat_status -> whose turn-change screen is up -> that seat's session gets "Turn N: your turn ..."
  agent:       begin_standin_turn(<its leader>) -> plays -> end_turn, which hands the game to the next seat's
               turn-change screen (after the AI civs move, at the end of a round) -> stops
The coordinator records every civilization's stats once a round (bench_stats, a tool the agents never see) and stops
at a win, at the turn limit, or when a STOP file appears in the run directory.

Accounts: each seat keeps one account for the whole game (the prompt cache belongs to the account), claimed like any
Kenso subagent unless --accounts gives a fixed list (one per seat). On a usage limit the seat's session moves to a new
account with its context intact.

Writes, in --runtime-dir/<game-id>/:
  game.json            title, settings and seats with their transcripts
  rounds.jsonl         one row per turn: every major civ's score, cities, yields, techs and civics, and the winner
  turns.jsonl          one row per seat turn: seconds, tokens, API-equivalent dollars, tries, how it ended
  seats/<seat>/        that agent's system.md, mcp.json, sessions.json and the raw stream-json events/ of each turn

    python3 tools/run_hotseat.py --game-id h1-four-opus --speed Online --turn-limit 250 \\
        --seat 0:LEADER_GILGAMESH:Opus-A --seat 1:LEADER_TRAJAN:Opus-B ...
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_game as rg  # noqa: E402
import timeline as tl  # noqa: E402

COORDINATOR_ONLY = ["bench_stats", "bench_launch_staged_game", "load_hotseat_save", "list_saves"]
TURN_PROMPT = 'Turn {turn}: your turn, {leader}. Call begin_standin_turn("{leader}"), play the turn, then end_turn once.'
NOT_ENDED = ('The game is still on your turn {turn}: it did not end, or it was reloaded to the start of the turn because '
             'the AI civs\' turn after it hung (tools/hotseat_doctor.py), which undoes your orders from that turn. Call '
             'begin_standin_turn("{leader}"), check what is done, finish the turn and call end_turn; when it reports '
             'that the turn ended, stop.')
STATUS_RE = re.compile(r"turn (\d+): local player is .*?\(slot (\d+), player name '(.*?)'\), turn active=(True|False)")


WHO_MANY = ("Several Claude agents share this game, each playing its own civilization, alongside civilizations run by "
            "the game's built-in AI. The game runs in hotseat mode: the agents take their turns one after another, then "
            "the AI civilizations move. Every other civilization is a rival, whether an agent or the AI runs it. You "
            "don't know which civilizations the other agents play.")
WHO_ONE = ("You are the only agent in this game: every other civilization is run by the game's built-in AI, and every "
           "one is a rival. The game runs in hotseat mode, so your turn arrives as a message, then the AI civilizations "
           "move.")
DEALS = ("- Deals and proposals you send to an agent's civilization are answered on that civilization's turn, not at "
         "once. Proposals from them show up in your pending trades and diplomacy. An agent may keep or break a promise, "
         "just as you may.\n")


def seat_system_prompt(seats: int = 2) -> str:
    speed = "\n".join(ln for ln in (rg.PROMPTS / "speed.md").read_text().splitlines() if "get_turn_briefing" not in ln)
    hotseat = (rg.PROMPTS / "hotseat.md").read_text().format(
        who=WHO_MANY if seats > 1 else WHO_ONE, deals=DEALS if seats > 1 else "")
    parts = [(rg.VENDOR / "AGENTS.md").read_text(), (rg.PROMPTS / "base-game.md").read_text(), speed, hotseat]
    return "\n\n".join(p.strip() for p in parts) + "\n"


class Seat(rg.Run):
    """One agent: a Run whose sessions are one turn each, in runs/<game>/seats/<name>/."""

    def __init__(self, a: argparse.Namespace, slot: int, leader: str, name: str):
        ns = argparse.Namespace(**vars(a))
        ns.game_id = f"{a.game_id}/seats/{name}"
        ns.accounts = [a.accounts[slot % len(a.accounts)]] if a.accounts else None
        super().__init__(ns)
        self.slot, self.leader, self.name = slot, leader, name
        self.slot_held = False  # Game.play holds one machine slot for the whole game
        self.acct: str | None = None

    def write_setup(self) -> None:
        (self.dir / "system.md").write_text(seat_system_prompt(len(self.a.seat)))
        (self.dir / "mcp.json").write_text(json.dumps({"mcpServers": {"civ6": {
            "type": "http", "url": self.a.mcp_url, "timeout": 900_000}}}, indent=2))
        (self.dir / "settings.json").write_text(json.dumps({"disableAllHooks": True}, indent=2))

    def write_manifest(self) -> None:  # the game's manifest is the coordinator's
        pass

    def claude_cmd(self, acct: str, prompt: str, resume: str | None) -> list[str]:
        return super().claude_cmd(acct, prompt, resume) + [
            "--disallowedTools", ",".join(f"mcp__civ6__{t}" for t in COORDINATOR_ONLY)]

    def kickoff(self, turn: int) -> str:
        a = self.a
        return (
            f"## Game: {a.title}\n\n"
            f"**Your leader:** {self.leader}\n**Difficulty of the AI civilizations:** {a.difficulty}\n"
            f"**Map:** {a.map}\n**Game speed:** {a.speed}\n**Turn limit:** {a.turn_limit}\n\n"
            "### Objective\n\nWin the game. Any victory type counts.\n\n"
            + TURN_PROMPT.format(turn=turn, leader=self.leader)
        )

    def play_turn(self, turn: int, retry: bool) -> dict:
        """One turn for this seat: resume its session (or start it) and wait until the agent stops."""
        if self.acct is None:
            self.acct = self.claim()
        last = self.sessions[-1] if self.sessions else None
        if last is None:
            prompt, resume = self.kickoff(turn), None
        elif last.get("session_id") and (src := rg.transcript_file(last)):
            if last["account"] != self.acct:
                rg.move_session(src, self.acct)  # same session, new account: the agent keeps its context
            prompt = (NOT_ENDED if retry else TURN_PROMPT).format(turn=turn, leader=self.leader)
            resume = last["session_id"]
        else:
            prompt, resume = rg.RESUME_PROMPT + "\n\n" + TURN_PROMPT.format(turn=turn, leader=self.leader), None
        slot = None
        if not self.a.accounts and not self.slot_held:
            slot = self.fleet.take_slot()
            self.fleet.stagger()
        try:
            row = self.run_session(self.acct, prompt, resume)
        finally:
            if slot:
                slot.close()
        if row.get("limit"):
            self.drop(self.acct, row["limit"]["resets"] or time.time() + 3600)
            self.acct = None
        return row


class Game:
    def __init__(self, a: argparse.Namespace):
        self.a = a
        self.dir = Path(a.runtime_dir).expanduser() / a.game_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.seats = {}
        for spec in a.seat:
            slot, leader, name = spec.split(":", 2)
            self.seats[int(slot)] = Seat(a, int(slot), leader, name)
        self.prices = tl.prices()
        # The war room reads civ6-mcp's files; the coordinator writes the same kinds here (tools/warroom/collect.py
        # --local-dir runs/<game>/telemetry): diary rows per civ and turn, a heartbeat, a game_over log row.
        self.tele = self.dir / "telemetry"
        self.tele.mkdir(exist_ok=True)
        self.key = f"hotseat_{a.seed}_{a.game_id}"
        self.started = rg.now()
        self.helper = rg.Run.__new__(rg.Run)  # only for its mcp() call
        self.helper.a = a

    def write_manifest(self) -> None:
        a = self.a
        manifest = {
            "title": a.title, "game_id": a.game_id, "mode": "hotseat", "effort": a.effort, "difficulty": a.difficulty,
            "map": a.map, "speed": a.speed, "turn_limit": a.turn_limit, "game_key": self.key,
            "started_at": self.started,
            "agents": [{"name": s.name, "pid": s.slot, "slot": s.slot, "leader": s.leader, "model": a.model,
                        "transcripts": [r["transcript"] for r in s.sessions if r.get("transcript")]}
                       for s in self.seats.values()],
        }
        tmp = self.dir / "game.json.tmp"
        tmp.write_text(json.dumps(manifest, indent=2))
        tmp.replace(self.dir / "game.json")

    def status(self) -> dict | None:
        out = self.helper.mcp("hotseat_status", timeout=60)
        m = STATUS_RE.search(out)
        if not m:
            return None
        return {"turn": int(m.group(1)), "slot": int(m.group(2)), "name": m.group(3), "active": m.group(4) == "True",
                "screen": "PlayerChange screen (Save Game / Start Turn) is showing" in out}

    def stats(self) -> dict | None:
        out = self.helper.mcp("bench_stats", timeout=60)
        line = next((ln for ln in out.splitlines() if ln.startswith("{")), "")  # not the "=== bench_stats {}" header
        try:
            return json.loads(line)
        except ValueError:
            return None

    def append(self, name: str, row: dict) -> None:
        with open(self.dir / name, "a") as f:
            f.write(json.dumps(row) + "\n")

    def reflections(self, seat: Seat) -> dict | None:
        """The agent's last end_turn reflections, from its newest events file."""
        files = sorted((seat.dir / "events").glob("*.jsonl"))
        for f in reversed(files[-2:]):
            found = None
            for ln in open(f):
                if '"end_turn"' not in ln:
                    continue
                try:
                    e = json.loads(ln)
                except ValueError:
                    continue
                for c in (e.get("message") or {}).get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name", "").endswith("__end_turn"):
                        found = c.get("input") or found
            if found:
                return found
        return None

    def write_telemetry(self, stats: dict, game_over: str | None = None) -> None:
        turn = stats.get("turn")
        by_slot = {s.slot: s for s in self.seats.values()}
        with open(self.tele / f"diary_{self.key}.jsonl", "a") as f:
            for p in stats.get("players", []):
                seat = by_slot.get(p["id"]) if p.get("human") else None
                row = {"turn": turn, "pid": p["id"], "civ": p["civ"], "leader": p["leader"], "is_agent": seat is not None,
                       "score": p["score"], "cities": p["cities"], "pop": p["pop"], "science": p["science"],
                       "culture": p["culture"], "gold": p["gold"], "military": p["military"],
                       "techs_completed": p["techs"], "civics_completed": p["civics"]}
                if seat is not None and (refl := self.reflections(seat)):
                    row["reflections"] = refl
                f.write(json.dumps(row) + "\n")
        hb = {"phase": "finished" if game_over else "playing", "turn": turn, "ts": time.time(), "run_id": self.a.game_id}
        (self.tele / "heartbeat.json.tmp").write_text(json.dumps(hb))
        (self.tele / "heartbeat.json.tmp").replace(self.tele / "heartbeat.json")
        if game_over:
            win = next((p for p in stats.get("players", []) if p["team"] == stats.get("winning_team")), {})
            with open(self.tele / f"log_{self.key}.jsonl", "a") as f:
                f.write(json.dumps({"type": "game_over", "turn": turn, "ts": time.time(), "outcome": {
                    "winner_civ": win.get("civ"), "winner_leader": win.get("leader"), "victory_type": None,
                    "detail": game_over}}) + "\n")

    def play(self) -> str:
        for s in self.seats.values():
            s.write_setup()
        self.write_manifest()
        warroom = None
        if self.a.warroom:
            log = open(self.dir / "warroom.stderr", "a")
            warroom = subprocess.Popen([sys.executable, str(rg.REPO / "tools" / "warroom" / "collect.py"), "--manifest",
                                        str(self.dir / "game.json"), "--out", str(Path(self.a.warroom).expanduser()),
                                        "--local-dir", str(self.tele), "--publish"], stdout=log, stderr=log)
        last_round, last_key, tries = -1, None, 0
        game_slot = None
        if not self.a.accounts:
            # Only one seat plays at a time, so the game holds one of the machine's headless slots from start to
            # end instead of queueing for a slot on every seat turn (minutes each on a busy machine).
            # The machine's launch stagger applies once, at the start, as for any run_on_account.py run: seats then
            # start one after another, and queueing behind every other launch on the box cost about 3 minutes a turn.
            fleet = next(iter(self.seats.values())).fleet
            game_slot = fleet.take_slot()
            fleet.stagger()
            for s in self.seats.values():
                s.slot_held = True
        try:
            while True:
                if (self.dir / "STOP").exists():
                    return "STOP file"
                st = self.status()
                if st is None:
                    time.sleep(10)
                    continue
                if st["turn"] != last_round:
                    stats = self.stats()
                    if stats:
                        self.append("rounds.jsonl", {"ts": time.time(), **stats})
                        last_round = st["turn"]
                        over = (f"team {stats['winning_team']} won on turn {stats.get('turn')}"
                                if stats.get("winning_team", -1) >= 0 else None)
                        self.write_telemetry(stats, over)
                        if over:
                            return f"game over: {over}"
                    if st["turn"] > self.a.turn_limit:
                        return f"turn limit {self.a.turn_limit} reached"
                seat = self.seats.get(st["slot"])
                if seat is None or not st["active"]:
                    time.sleep(5)  # the AI civs are moving, or a screen is loading
                    continue
                key = (st["turn"], st["slot"])
                tries = tries + 1 if key == last_key else 0
                last_key = key
                if tries >= self.a.max_tries:
                    return f"{seat.name} did not end turn {st['turn']} after {tries} tries"
                print(f"run_hotseat: turn {st['turn']}, {seat.name} ({seat.leader})" + (f", try {tries + 1}" if tries else ""),
                      file=sys.stderr)
                t0 = time.time()
                row = seat.play_turn(st["turn"], retry=tries > 0)
                usage = row.get("usage") or {}
                self.append("turns.jsonl", {
                    "turn": st["turn"], "seat": seat.name, "slot": seat.slot, "leader": seat.leader, "try": tries + 1,
                    "account": row.get("account"), "session": row.get("n"), "start": t0, "end": time.time(),
                    "seconds": round(time.time() - t0, 1), "requests": row.get("num_turns"),
                    "input": usage.get("input_tokens"), "output": usage.get("output_tokens"),
                    "cache_read": usage.get("cache_read_input_tokens"),
                    "cache_write": usage.get("cache_creation_input_tokens"),
                    "usd": round(tl.usd(self.a.model, usage, self.prices) or 0, 4),
                    "is_error": row.get("is_error"), "limit": row.get("limit"), "result": (row.get("result") or "")[:300],
                })
                self.write_manifest()
                if row.get("exit_code") and not row.get("session_id"):
                    return f"claude failed to start for {seat.name} (exit {row['exit_code']}): {row.get('result')}"
                if row.get("is_error") and not row.get("limit") and rg.seconds(row) < 120:
                    time.sleep(60)  # a quick failure (API overload, network): don't spin
        finally:
            if game_slot:
                game_slot.close()
            for s in self.seats.values():
                s.release(s.acct)
            if warroom:
                warroom.terminate()


HOTSEAT_LEADERS = ["LEADER_GILGAMESH", "LEADER_TRAJAN", "LEADER_GORGO", "LEADER_PEDRO",
                   "LEADER_BARBAROSSA", "LEADER_T_ROOSEVELT", "LEADER_CLEOPATRA", "LEADER_PHILIP_II"]  # lua/new-hotseat.lua


def prepare(a: argparse.Namespace, game: "Game") -> None:
    """Make a fresh hotseat game on the game PC and start it: the hotseat server's env file, the game hosted from the
    main menu by windows/new-start.ps1 + lua/new-hotseat.lua (one human seat per agent, AI in the rest), the server
    restarted in hotseat mode, and the staging room launched through the bridge."""
    slots = sorted(game.seats)
    if slots != list(range(len(slots))) or any(game.seats[i].leader != HOTSEAT_LEADERS[i] for i in slots):
        raise SystemExit(f"run_hotseat: --prepare needs seats 0..n-1 with the leaders of lua/new-hotseat.lua: "
                         f"{HOTSEAT_LEADERS[:len(slots)]}")
    remote = rg.REPO / "remote"
    env = {"CIV_MCP_DISABLE_LUA": "1", "CIV_MCP_AGENT_MODEL": a.model, "CIV_MCP_SERVER": "hotseat",
           "CIV_MCP_RUN_ID": a.game_id}
    write = (f"Set-Content -Path (Join-Path $env:USERPROFILE 'civ6-bench\\mcp-env.json') -Value '{json.dumps(env)}' "
             "-Encoding UTF8; 'env written'")
    print(subprocess.run([str(remote / "zps.sh"), "-c", write], capture_output=True, text=True).stdout.strip(),
          file=sys.stderr)
    script = game.dir / "new-start.ps1"
    script.write_text(f"$Speed = 'GAMESPEED_{a.speed.upper()}'; $Seed = {a.seed}; $LuaFile = 'new-hotseat.lua'; "
                      f"$Extra = 'HUMANS = {len(slots)}'\n" + (rg.REPO / "windows" / "new-start.ps1").read_text())
    out = subprocess.run([str(remote / "zexec.sh"), str(script), "740"], capture_output=True, text=True).stdout
    print(out.strip(), file=sys.stderr)
    if "hotseat game hosted" not in out:
        raise SystemExit("run_hotseat: --prepare could not host the hotseat game")
    out = subprocess.run([str(remote / "zexec.sh"), str(rg.REPO / "windows" / "restart-mcp-http.ps1"), "180"],
                         capture_output=True, text=True).stdout
    print(f"run_hotseat: {out.strip()}", file=sys.stderr)
    out = game.helper.mcp("bench_launch_staged_game", timeout=600)
    print(f"run_hotseat: {out.strip()}", file=sys.stderr)
    if "Started in" not in out:
        raise SystemExit("run_hotseat: --prepare could not start the staged game")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-id", required=True)
    ap.add_argument("--seat", action="append", required=True, metavar="SLOT:LEADER:NAME",
                    help="one hotseat seat an agent plays, e.g. 0:LEADER_GILGAMESH:opus-a (repeat per seat)")
    ap.add_argument("--accounts", type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
                    help="fixed accounts, one per seat in slot order, instead of claiming from the Claude Accounts sheet")
    ap.add_argument("--use-case", default="Development")
    ap.add_argument("--title", default="Four Opus 5.5 agents and four built-in AI civs, hotseat")
    ap.add_argument("--difficulty", default="Prince")
    ap.add_argument("--map", default="Pangaea, standard size")
    ap.add_argument("--speed", default="Online")
    ap.add_argument("--turn-limit", type=int, default=250)
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--mcp-url", default="http://127.0.0.1:18771/mcp")
    ap.add_argument("--claude-cmd", help="default: claude under ~/.claude-{account}; with --accounts, claude-acct {account}")
    ap.add_argument("--runtime-dir", default="~/.civ6-bench/runs")
    ap.add_argument("--max-tries", type=int, default=4, help="resumes per seat turn before the game stops")
    ap.add_argument("--seed", type=int, default=20261106, help="the map seed, for the war room's file key")
    ap.add_argument("--warroom", help="also run the war room collector, publishing the page to this folder")
    ap.add_argument("--print-prompts", action="store_true")
    ap.add_argument("--prepare", action="store_true",
                    help="make a fresh hotseat game on the game PC first (kills the running game)")
    a = ap.parse_args()
    if not a.claude_cmd:
        # Game.play holds one machine slot for the whole game, as run_on_account.py does for its run, so claude starts
        # straight under the account's config dir. Through claude-acct it would wait for a second slot (claude-slot)
        # on every seat turn: about 5 minutes each on a busy machine.
        a.claude_cmd = ("claude-acct {account}" if a.accounts
                        else f"env CLAUDE_CONFIG_DIR={Path.home()}/.claude-{{account}} claude")
    # Run (run_game.py) reads these; the hotseat game has no civ6-mcp files of its own.
    a.track, a.goal, a.game_key, a.run_id, a.civ6mcp_dir, a.civ = "standard", None, a.game_id, a.game_id, "", ""
    fresh, a.prepare = a.prepare, False
    a.agent_name, a.max_sessions, a.load_save, a.start_save = "", 10**6, None, None
    game = Game(a)
    if a.print_prompts:
        print(seat_system_prompt(len(a.seat)))
        print("=" * 80)
        print(next(iter(game.seats.values())).kickoff(1))
        return
    if fresh:
        prepare(a, game)
    why = game.play()
    print(f"run_hotseat: stopped: {why}", file=sys.stderr)


if __name__ == "__main__":
    main()
