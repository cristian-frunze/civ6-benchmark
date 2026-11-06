#!/usr/bin/env python3
"""Civ 6 war room collector.

Reads a game manifest, gathers civ6-mcp telemetry (diary, tool log, map
capture, heartbeat) plus each agent's Claude Code transcripts, and atomically
writes state.json for the war room page in warroom/.

    python3 tools/warroom/collect.py --manifest game.json \
        --out ~/tailscale-share/civ6-warroom [--local-dir DIR] \
        [--interval 3] [--once] [--publish]

Without --local-dir the civ6-mcp files come from the game PC through
remote/zps.sh, read incrementally from byte offsets. Stdlib only, Python 3.11+.
The schema of state.json is documented in warroom/README.md.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
PAGE_DIR = REPO / "warroom"
PAGE_FILES = ["index.html", "style.css", "app.js"]
PAGE_DIRS = ["fonts"]
ZPS = REPO / "remote" / "zps.sh"

STATE_VERSION = 1
ANCHOR = 256  # bytes kept before each offset to detect rewritten files
CHUNK_CAP = 3 * 1024 * 1024  # max bytes per file per fetch
FETCH_BUDGET = 6 * 1024 * 1024  # max bytes per remote round trip
LOG_TAIL_FROM = 2 * 1024 * 1024  # on first sight, read big logs from the last 2 MB only
WHOLE_CAP = 8 * 1024 * 1024  # max size for whole-file JSON reads
SPARK_POINTS = 120
TOOL_HISTORY = 10  # the page shows 6, more in tall panes
STALE_AFTER_S = 15 * 60

MAJOR_COLORS = [
    "#ff5d47", "#3db8ff", "#ffc53d", "#a77bff", "#31d8a5", "#ff7eb6",
    "#ff9b3d", "#e9e4d8", "#8fd14f", "#4f7bff", "#c9a77c", "#e05cff",
]
CS_COLORS = {
    "Scientific": "#5f86b8", "Cultural": "#8e6aa3", "Militaristic": "#a65050",
    "Religious": "#b9b4a8", "Trade": "#b3a24a", "Industrial": "#b07a45",
}
WAIT_TOOLS = {"end_turn"}
REFLECTION_KEYS = ("tactical", "strategic", "planning")
DIARY_KEEP = (
    "turn", "pid", "civ", "leader", "is_agent", "score", "cities", "pop",
    "science", "culture", "gold", "gold_per_turn", "faith_per_turn", "military",
    "era", "government", "techs_completed", "civics_completed", "sci_vp",
    "tourism", "reflections", "agent_model", "timestamp",
)

FILE_RE = re.compile(r"^(diary|log|mapturns|mapstatic)_(.+)\.(jsonl|json)$")
KEY_RE = re.compile(r"^(.+?_-?\d+)(?:_[^_]+)?$")
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.\-]+$")


# ── privacy ─────────────────────────────────────────────────────────────


class Sanitizer:
    """Redacts emails, paths, IPs, tailnet names and known host/user names."""

    def __init__(self, extra_words: list[str]):
        self.rules = [
            (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[email]"),
            (re.compile(r"\b[A-Za-z]:\\[^\s'\"`<>|]*"), "[path]"),
            (re.compile(r"\\\\[\w.-]+\\[^\s'\"`<>|]*"), "[path]"),
            (re.compile(r"(?<![\w:/.])~?/[\w.@+-]+/[^\s'\"`<>|)\]]*"), "[path]"),
            (re.compile(r"(?<![\w:/.])~/[^\s'\"`<>|)\]]*"), "[path]"),
            (re.compile(r"\b[\w-]+(?:\.[\w-]+)*\.ts\.net\b", re.I), "[host]"),
            (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[ip]"),
        ]
        words = sorted({w for w in extra_words if w and len(w) >= 3}, key=len, reverse=True)
        if words:
            alt = "|".join(re.escape(w) for w in words)
            self.rules.append((re.compile(rf"(?<![\w-])(?:{alt})(?![\w-])", re.I), "[redacted]"))

    def text(self, s: str) -> str:
        for rx, rep in self.rules:
            s = rx.sub(rep, s)
        return s

    def walk(self, obj: Any, skip: frozenset[str] = frozenset()) -> Any:
        if isinstance(obj, str):
            return self.text(obj)
        if isinstance(obj, list):
            return [self.walk(v, skip) for v in obj]
        if isinstance(obj, dict):
            return {k: (v if k in skip else self.walk(v, skip)) for k, v in obj.items()}
        return obj


def sanitizer_for(manifest: dict) -> Sanitizer:
    words = [os.environ.get("CIV_HOST") or "zenbook", socket.gethostname(), socket.gethostname().split(".")[0]]
    words += os.environ.get("WARROOM_REDACT", "").split(",")
    try:
        words.append(getpass.getuser())
    except Exception:
        pass
    m = re.search(r"\\Users\\([^\\]+)", str(manifest.get("civ6mcp_dir") or ""), re.I)
    if m:
        words.append(m.group(1))
    return Sanitizer(words)


# ── incremental file tails ──────────────────────────────────────────────


@dataclass
class Tail:
    """Byte-offset tail of an append-only JSONL file, with rewrite detection."""

    offset: int = 0
    anchor: bytes = b""
    skip_partial: bool = False
    seen: bool = False

    def reset(self) -> None:
        self.offset, self.anchor, self.skip_partial = 0, b"", False

    def plan(self, size: int, tail_from: int | None = None) -> tuple[int, int] | None:
        if not self.seen:
            self.seen = True
            if tail_from is not None and size > tail_from * 2:
                self.offset, self.anchor, self.skip_partial = size - tail_from, b"", True
        if size < self.offset:
            self.reset()
        if size == self.offset:
            return None
        start = self.offset - len(self.anchor)
        return start, min(size - start, CHUNK_CAP)

    def apply(self, start: int, data: bytes) -> tuple[list[bytes], bool]:
        """Consume a chunk read from `start`. Returns (complete lines, was_reset)."""
        keep = self.offset - start
        if keep < 0 or data[:keep] != self.anchor:
            self.reset()  # file was rewritten: re-read from 0 next time
            return [], True
        new = data[keep:]
        cut = new.rfind(b"\n")
        if cut < 0:
            if len(data) >= CHUNK_CAP:  # read was capped inside one absurdly long line: skip it
                self.offset += len(new)
                self.anchor = data[-ANCHOR:]
                self.skip_partial = True
            return [], False
        done = new[: cut + 1]
        self.offset += len(done)
        self.anchor = data[: keep + len(done)][-ANCHOR:]
        lines = done.split(b"\n")
        if self.skip_partial:
            lines = lines[1:]
            self.skip_partial = False
        return [ln for ln in lines if ln.strip()], False


def parse_json_lines(lines: list[bytes]) -> list[dict]:
    out = []
    for ln in lines:
        try:
            obj = json.loads(ln)
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


# ── sources: local folder or the game PC over SSH ───────────────────────


@dataclass
class Fetch:
    ok: bool = True
    has_dir: bool = True
    error: str | None = None
    files: dict[str, tuple[int, float]] = field(default_factory=dict)  # name -> (size, mtime)
    chunks: dict[str, tuple[int, bytes]] = field(default_factory=dict)  # name -> (start, data)


class LocalSource:
    def __init__(self, path: Path):
        self.path = path

    def fetch(self, reads: dict[str, tuple[int, int]]) -> Fetch:
        f = Fetch()
        if not self.path.is_dir():
            f.has_dir = False
            return f
        for e in os.scandir(self.path):
            if e.is_file():
                st = e.stat()
                f.files[e.name] = (st.st_size, st.st_mtime)
        for name, (start, length) in reads.items():
            try:
                with open(self.path / name, "rb") as fh:
                    fh.seek(start)
                    f.chunks[name] = (start, fh.read(length))
            except OSError:
                pass
        return f


class RemoteSource:
    """Lists and reads files in the civ6-mcp folder on the game PC, one SSH call per fetch.

    The script only lists that folder and reads byte ranges of files in it.
    """

    def __init__(self, win_dir: str | None):
        self.win_dir = win_dir

    def script(self, reads: dict[str, tuple[int, int]]) -> str:
        if self.win_dir:
            # %USERPROFILE%-style paths expand on the game PC; $env:USERPROFILE is accepted for older manifests.
            w = self.win_dir.replace("$env:USERPROFILE", "%USERPROFILE%").replace("'", "''")
            d = f"[Environment]::ExpandEnvironmentVariables('{w}')"
        else:
            d = "(Join-Path $env:USERPROFILE '.civ6-mcp')"
        req = "\n".join(
            f"[void]$reqs.Add(@('{n}', {s}, {ln}))"
            for n, (s, ln) in reads.items()
            if SAFE_NAME.match(n)
        )
        return f"""
$d = {d}
if (-not (Test-Path -LiteralPath $d -PathType Container)) {{ 'WR|NODIR'; return }}
'WR|DIR'
foreach ($p in [IO.Directory]::GetFiles($d)) {{
  $i = New-Object IO.FileInfo $p
  'F|' + $i.Name + '|' + $i.Length + '|' + $i.LastWriteTimeUtc.ToFileTimeUtc()
}}
$reqs = New-Object System.Collections.ArrayList
{req}
foreach ($r in $reqs) {{
  try {{
    $fs = [IO.File]::Open((Join-Path $d $r[0]), [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]'ReadWrite, Delete')
    try {{
      $len = $fs.Length; $start = [long]$r[1]; if ($start -gt $len) {{ $start = $len }}
      $n = [int][Math]::Min([long]$r[2], $len - $start)
      $buf = New-Object byte[] $n
      [void]$fs.Seek($start, [IO.SeekOrigin]::Begin)
      $got = 0
      while ($got -lt $n) {{ $k = $fs.Read($buf, $got, $n - $got); if ($k -le 0) {{ break }}; $got += $k }}
      'C|' + $r[0] + '|' + $start + '|' + [Convert]::ToBase64String($buf, 0, $got)
    }} finally {{ $fs.Dispose() }}
  }} catch {{ 'X|' + $r[0] }}
}}
'WR|END'
"""

    def fetch(self, reads: dict[str, tuple[int, int]]) -> Fetch:
        try:
            out = subprocess.run(
                [str(ZPS), "-c", self.script(reads)],
                capture_output=True, timeout=90, check=False,
            ).stdout.decode("utf-8", "replace")
        except (OSError, subprocess.TimeoutExpired) as e:
            return Fetch(ok=False, error=f"game PC unreachable ({type(e).__name__})")
        return parse_remote(out)


def parse_remote(out: str) -> Fetch:
    """Parse the WR|/F|/C| lines printed by RemoteSource.script."""
    f = Fetch()
    lines = [ln.strip("\r") for ln in out.split("\n")]
    if "WR|NODIR" in lines:
        f.has_dir = False
        return f
    if "WR|END" not in lines:
        return Fetch(ok=False, error="game PC unreachable or script failed")
    for ln in lines:
        parts = ln.split("|")
        try:
            if parts[0] == "F" and len(parts) == 4:
                ft = int(parts[3])  # Windows FILETIME: 100 ns ticks since 1601
                f.files[parts[1]] = (int(parts[2]), (ft - 116444736000000000) / 1e7)
            elif parts[0] == "C" and len(parts) == 4:
                f.chunks[parts[1]] = (int(parts[2]), base64.b64decode(parts[3]))
        except ValueError:
            continue
    return f


# ── civ6-mcp telemetry ──────────────────────────────────────────────────


def nice_city(raw: str | None) -> str:
    """civ6-mcp records city names as localization keys (LOC_CITY_NAME_SAN_FRANCISCO): show "San Francisco"."""
    s = (raw or "").strip()
    if s.upper().startswith("LOC_CITY_NAME_"):
        s = " ".join(w.capitalize() for w in s[len("LOC_CITY_NAME_"):].split("_"))
    return s


def nice_civ(raw: str | None) -> str:
    s = (raw or "").strip()
    for p in ("CIVILIZATION_", "LEADER_"):
        if s.upper().startswith(p):
            s = s[len(p):]
    if s.isupper() or "_" in s:
        s = " ".join(w.capitalize() for w in s.replace("_", " ").split())
    return s or "Unknown"


def key_match(rest: str, keys: list[str]) -> bool:
    return any(rest == k or rest.startswith(k + "_") for k in keys)


def file_key(rest: str) -> str:
    rest = rest.removesuffix("_cities")
    m = KEY_RE.match(rest)
    return m.group(1) if m else rest


def num(v: Any) -> float | None:
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def parse_ts(v: Any) -> float | None:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str) and v:
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


class Telemetry:
    """Incremental view of one game's civ6-mcp files."""

    def __init__(self, source: LocalSource | RemoteSource):
        self.source = source
        self.keys: list[str] = []
        self.tails: dict[str, Tail] = {}
        self.whole: dict[str, tuple[int, float]] = {}  # name -> (size, mtime) last read
        self.files: dict[str, tuple[int, float]] = {}
        self.diary: dict[str, dict[tuple[int, int], dict]] = {}
        self.logs: dict[str, deque] = {}
        self.log_turn: dict[str, int] = {}
        self.game_over: dict | None = None
        self.mapstatic: dict[str, dict] = {}
        self.mapturns: dict[str, list[dict]] = {}
        self.heartbeat: dict | None = None
        self.status = {"ok": False, "folder": False, "error": None, "files": 0, "note": None}

    def kind_of(self, name: str) -> str | None:
        if name == "heartbeat.json":
            return "heartbeat"
        m = FILE_RE.match(name)
        if not m:
            return None
        kind, rest, ext = m.groups()
        if kind == "diary" and rest.endswith("_cities"):
            return None
        if (kind == "mapstatic") != (ext == "json"):
            return None
        if not key_match(rest, self.keys):
            return None
        return kind

    def auto_key(self) -> str | None:
        best = None
        for name, (_, mtime) in self.files.items():
            m = FILE_RE.match(name)
            if m and m.group(1) in ("diary", "log") and not m.group(2).endswith("_cities"):
                if best is None or mtime > best[0]:
                    best = (mtime, file_key(m.group(2)))
        return best[1] if best else None

    def plan_reads(self) -> tuple[dict[str, tuple[int, int]], bool]:
        """Byte ranges to fetch next, and whether they are worth an extra round trip now.

        Reads ask for up to the cap, so the remote side returns everything up to the
        file's current end, not just up to the size seen in the last listing.
        """
        reads: dict[str, tuple[int, int]] = {}
        budget, urgent = FETCH_BUDGET, False
        order = {"heartbeat": 0, "mapstatic": 1, "diary": 2, "mapturns": 3, "log": 4}
        tracked = [(order[k], n) for n in self.files if (k := self.kind_of(n))]
        newest_static = self.latest_static_name()
        for _, name in sorted(tracked):
            kind = self.kind_of(name)
            size, mtime = self.files[name]
            if kind in ("heartbeat", "mapstatic"):
                if kind == "mapstatic" and name != newest_static:
                    continue
                if self.whole.get(name) == (size, mtime) or size > WHOLE_CAP or size > budget:
                    continue
                urgent |= name not in self.whole
                reads[name] = (0, WHOLE_CAP)
                budget -= size
                continue
            tail = self.tails.setdefault(name, Tail())
            fresh = not tail.seen
            plan = tail.plan(size, LOG_TAIL_FROM if kind == "log" else None)
            if plan and budget > 0:
                start, need = plan
                urgent |= fresh or need > 64 * 1024
                reads[name] = (start, CHUNK_CAP if budget >= CHUNK_CAP else max(budget, ANCHOR + 1))
                budget -= need
        return reads, urgent

    def latest_static_name(self) -> str | None:
        names = [n for n in self.files if self.kind_of(n) == "mapstatic"]
        return max(names, key=lambda n: self.files[n][1]) if names else None

    def poll(self, manifest_keys: list[str]) -> None:
        for _ in range(3):  # extra round trips only for new files or a capped chunk
            reads, _ = self.plan_reads()
            got = self.source.fetch(reads)
            if not got.ok:
                self.status.update(ok=False, error=got.error)
                return
            self.status.update(ok=True, error=None, folder=got.has_dir)
            self.files = got.files
            keys, note = manifest_keys, None
            if keys and not any((m := FILE_RE.match(n)) and key_match(m.group(2), keys) for n in self.files):
                if auto := self.auto_key():  # e.g. the runner guessed the key: follow the newest game instead
                    keys, note = [auto], f"game_key matched no files, showing {auto}"
            elif not keys:
                keys = [k] if (k := self.auto_key()) else []
            self.status["note"] = note
            if keys != self.keys:
                self.keys = keys
                self.reset_all()
            self.status["files"] = sum(1 for n in self.files if self.kind_of(n))
            for name, (start, data) in got.chunks.items():
                self.ingest(name, start, data)
            if not self.plan_reads()[1]:
                return

    def reset_all(self) -> None:
        self.tails.clear()
        self.whole.clear()
        self.diary.clear()
        self.logs.clear()
        self.log_turn.clear()
        self.mapstatic.clear()
        self.mapturns.clear()
        self.game_over = None

    def ingest(self, name: str, start: int, data: bytes) -> None:
        kind = self.kind_of(name)
        if kind in ("heartbeat", "mapstatic"):
            self.whole[name] = self.files.get(name, (0, 0.0))
            try:
                obj = json.loads(data)
            except ValueError:
                self.whole.pop(name, None)  # caught mid-write: retry next cycle
                return
            if kind == "heartbeat":
                self.heartbeat = obj
            else:
                self.mapstatic[name] = obj
            return
        tail = self.tails.get(name)
        if tail is None:
            return
        lines, was_reset = tail.apply(start, data)
        if was_reset:
            return  # rewritten in place: keep showing old rows until the re-read from 0 lands
        if start == 0:  # a full (re-)read replaces this file's rows; diary rows are keyed and simply overwrite
            self.logs.pop(name, None)
            self.log_turn.pop(name, None)
            self.mapturns.pop(name, None)
        rows = parse_json_lines(lines)
        if kind == "diary":
            store = self.diary.setdefault(name, {})
            for r in rows:
                if isinstance(r.get("turn"), int) and isinstance(r.get("pid"), int):
                    store[(r["turn"], r["pid"])] = {k: r[k] for k in DIARY_KEEP if k in r}
        elif kind == "log":
            store = self.logs.setdefault(name, deque(maxlen=200))
            for r in rows:
                slim = {k: r.get(k) for k in ("type", "tool", "turn", "ts", "success", "duration_ms")}
                if r.get("type") == "game_over" and isinstance(r.get("outcome"), dict):
                    slim["outcome"] = r["outcome"]
                    self.game_over = slim
                store.append(slim)
                if isinstance(r.get("turn"), int):
                    self.log_turn[name] = max(self.log_turn.get(name, 0), r["turn"])
        elif kind == "mapturns":
            self.mapturns.setdefault(name, []).extend(r for r in rows if isinstance(r.get("turn"), int))

    # merged views

    def diary_rows(self) -> dict[tuple[int, int], dict]:
        merged: dict[tuple[int, int], dict] = {}
        for name in sorted(self.diary, key=lambda n: self.files.get(n, (0, 0.0))[1]):
            for key, row in self.diary[name].items():
                old = merged.get(key)
                if old is None or row.get("is_agent") or not old.get("is_agent"):
                    merged[key] = row
        return merged

    def current_turn(self) -> int | None:
        turns = list(self.log_turn.values()) + [t for t, _ in self.diary_rows()]
        hb_turn = (self.heartbeat or {}).get("turn")
        if isinstance(hb_turn, int) and hb_turn > 0:  # 0 means "not known yet"
            turns.append(hb_turn)
        return max(turns) if turns else None

    def first_ts(self) -> float | None:
        ts = [e["ts"] for q in self.logs.values() for e in q if isinstance(e.get("ts"), (int, float))]
        return min(ts) if ts else None

    def map_state(self) -> dict | None:
        if not self.mapstatic:
            return None
        name = max(self.mapstatic, key=lambda n: (self.mapstatic[n].get("initialTurn") or 0, self.files.get(n, (0, 0.0))[1]))
        st = self.mapstatic[name]
        w, h = st.get("gridW") or 0, st.get("gridH") or 0
        flat = st.get("terrain") or []
        n = w * h
        if not n or len(flat) < n * 6:
            return None
        base = st.get("initialTurn") or 0
        owners = list(st.get("initialOwners") or [-1] * n)[:n]
        owners += [-1] * (n - len(owners))
        cities = st.get("initialCities") or []
        deltas = sorted((r for rows in self.mapturns.values() for r in rows if r["turn"] >= base), key=lambda r: r["turn"])
        for r in deltas:
            o = r.get("owners") or []
            for i in range(0, len(o) - 1, 2):
                if 0 <= o[i] < n:
                    owners[o[i]] = o[i + 1]
            if r.get("cities"):
                cities = r["cities"]
        try:
            terrain = bytes(255 if not (0 <= flat[i * 6] < 255) else flat[i * 6] for i in range(n))
            features = bytes(0 if flat[i * 6 + 1] < 0 else min(flat[i * 6 + 1] + 1, 255) for i in range(n))
            rivers = bytes(1 if flat[i * 6 + 3] else 0 for i in range(n))
            own = bytes(o + 1 if isinstance(o, int) and 0 <= o < 254 else 0 for o in owners)
        except (TypeError, ValueError):
            return None
        city_list = [
            {"x": c.get("x"), "y": c.get("y"), "pid": c.get("pid"), "pop": c.get("pop"), "name": nice_city(c.get("name"))}
            for c in cities if isinstance(c, dict)
        ]
        rev = hashlib.sha1(own + json.dumps(city_list).encode()).hexdigest()[:10]
        return {
            "w": w, "h": h, "wrap_x": True, "rev": rev,
            "terrain": base64.b64encode(terrain).decode(),
            "features": base64.b64encode(features).decode(),
            "rivers": base64.b64encode(rivers).decode(),
            "owners": base64.b64encode(own).decode(),
            "cities": city_list,
            "players": st.get("players") or [],
        }


# ── Claude Code transcripts ─────────────────────────────────────────────


def short_tool(name: str) -> str:
    if name.startswith("mcp__"):
        parts = name.split("__")
        return "__".join(parts[2:]) or name
    return name


def summarize_input(name: str, inp: Any) -> str:
    if not isinstance(inp, dict):
        return ""
    if name == "Bash":
        return str(inp.get("description") or inp.get("command") or "")[:90]
    if short_tool(name) == "end_turn":  # its arguments are the reflections, shown from the diary
        return ""
    if isinstance(inp.get("file_path"), str):  # Read / Write / Edit: the file name is enough
        return Path(inp["file_path"]).name
    bits = []
    for k, v in inp.items():
        if isinstance(v, str):
            v = v.replace("\n", " ")
            v = v if len(v) <= 28 else v[:27] + "…"
        elif isinstance(v, (int, float, bool)) or v is None:
            v = json.dumps(v)
        else:
            v = json.dumps(v, separators=(",", ":"))
            v = v if len(v) <= 24 else v[:23] + "…"
        bits.append(f"{k}={v}")
    s = ", ".join(bits)
    return s if len(s) <= 90 else s[:89] + "…"


class Transcript:
    """Incremental parse of one Claude Code JSONL transcript."""

    def __init__(self, path: Path, usage_only: bool = False):
        self.path = path
        self.usage_only = usage_only
        self.tail = Tail()
        self.size = -1
        self.reset()

    def reset(self) -> None:
        self.usage: dict[str, tuple] = {}  # message id -> (model, in, out, cache_read, cw5m, cw1h)
        self.tools: dict[str, dict] = {}
        self.order: deque = deque(maxlen=40)
        self.reasoning: deque = deque(maxlen=4)  # latest thinking-or-text per assistant message
        self.first_ts: float | None = None
        self.last_ts: float | None = None
        self.last_role: str | None = None
        self.last_stop: str | None = None
        self.model: str | None = None

    def update(self) -> None:
        try:
            size = self.path.stat().st_size
        except OSError:
            return
        while True:
            plan = self.tail.plan(size)
            if not plan:
                return
            start, length = plan
            with open(self.path, "rb") as fh:
                fh.seek(start)
                data = fh.read(length)
            lines, was_reset = self.tail.apply(start, data)
            if was_reset:
                self.reset()
                continue
            if not lines and self.tail.offset - len(self.tail.anchor) == start:
                return  # no complete line yet
            for e in parse_json_lines(lines):
                self.line(e)

    def line(self, e: dict) -> None:
        kind = e.get("type")
        if kind not in ("assistant", "user"):
            return
        msg = e.get("message") or {}
        ts = parse_ts(e.get("timestamp"))
        if kind == "assistant":
            mid = msg.get("id")
            u = msg.get("usage")
            model = msg.get("model") or ""
            if mid and isinstance(u, dict) and model != "<synthetic>":
                cc = u.get("cache_creation") or {}
                cw = u.get("cache_creation_input_tokens") or 0
                cw1 = cc.get("ephemeral_1h_input_tokens") or 0
                cw5 = cc.get("ephemeral_5m_input_tokens") if cc else cw
                self.usage[mid] = (
                    model, u.get("input_tokens") or 0, u.get("output_tokens") or 0,
                    u.get("cache_read_input_tokens") or 0, cw5 or 0, cw1,
                )
                self.model = model
        if self.usage_only or e.get("isSidechain"):
            return
        if ts is not None:
            self.first_ts = ts if self.first_ts is None else min(self.first_ts, ts)
            self.last_ts = ts if self.last_ts is None else max(self.last_ts, ts)
        self.last_role = kind
        content = msg.get("content")
        if kind == "assistant":
            self.last_stop = msg.get("stop_reason")
            mid = msg.get("id")
            for b in content if isinstance(content, list) else []:
                t = b.get("type")
                kind, text = None, ""
                if t == "thinking" and (b.get("thinking") or "").strip():
                    kind, text = "thinking", b["thinking"]
                elif t == "text" and (b.get("text") or "").strip():
                    kind, text = "text", b["text"]
                if kind:
                    last = self.reasoning[-1] if self.reasoning else None
                    entry = {"kind": kind, "text": text.strip()[:2400], "ts": ts, "mid": mid}
                    if last and last["mid"] == mid:
                        if not (last["kind"] == "thinking" and kind == "text"):  # thinking wins within a message
                            self.reasoning[-1] = entry
                    else:
                        self.reasoning.append(entry)
                elif t == "tool_use" and b.get("id"):
                    name = short_tool(b.get("name") or "?")
                    self.tools[b["id"]] = {
                        "name": name, "args": summarize_input(b.get("name") or "", b.get("input")),
                        "ts": ts, "ok": None, "done_ts": None,
                    }
                    self.order.append(b["id"])
        else:
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    rec = self.tools.get(b.get("tool_use_id"))
                    if rec:
                        rec["ok"] = not b.get("is_error")
                        rec["done_ts"] = ts
        if len(self.tools) > 80:  # keep memory flat over long games
            self.tools = {k: self.tools[k] for k in self.order if k in self.tools}

    def pending(self) -> list[dict]:
        return [self.tools[i] for i in self.order if i in self.tools and self.tools[i]["ok"] is None]


class AgentFeed:
    def __init__(self) -> None:
        self.transcripts: dict[str, Transcript] = {}

    def sync(self, paths: list[str]) -> list[Transcript]:
        out = []
        for p in paths:
            path = Path(os.path.expanduser(p))
            main = self.transcripts.setdefault(str(path), Transcript(path))
            main.update()
            out.append(main)
            sub = path.with_suffix("") / "subagents"
            if sub.is_dir():
                for f in sorted(sub.glob("*.jsonl")):
                    t = self.transcripts.setdefault(str(f), Transcript(f, usage_only=True))
                    t.update()
                    out.append(t)
        return out


def load_prices() -> dict:
    try:
        data = json.loads((PAGE_DIR / "prices.json").read_text())
        return {k: v for k, v in data.items() if isinstance(v, dict)}
    except (OSError, ValueError):
        return {}


def price_for(prices: dict, model: str) -> dict | None:
    if model in prices:
        return prices[model]
    hits = [k for k in prices if model.startswith(k)]
    return prices[max(hits, key=len)] if hits else None


def usage_totals(transcripts: list[Transcript], prices: dict) -> dict:
    seen: dict[str, tuple] = {}
    for t in transcripts:
        seen.update(t.usage)
    tot = {"input": 0, "output": 0, "cache_read": 0, "cache_write_5m": 0, "cache_write_1h": 0}
    usd, unpriced = 0.0, 0
    for model, i, o, cr, c5, c1 in seen.values():
        tot["input"] += i
        tot["output"] += o
        tot["cache_read"] += cr
        tot["cache_write_5m"] += c5
        tot["cache_write_1h"] += c1
        p = price_for(prices, model)
        if p:
            usd += (i * p.get("input", 0) + o * p.get("output", 0) + cr * p.get("cache_read", 0)
                    + c5 * p.get("cache_write_5m", 0) + c1 * p.get("cache_write_1h", 0)) / 1e6
        else:
            unpriced += i + o + cr + c5 + c1
    tot["total"] = sum(tot.values())
    tot["requests"] = len(seen)
    tot["usd"] = round(usd, 4) if prices else None
    tot["unpriced_tokens"] = unpriced
    return tot


def agent_activity(transcripts: list[Transcript], game_over: bool) -> dict:
    mains = [t for t in transcripts if not t.usage_only and t.last_ts is not None]
    if game_over:
        status = "done"
    elif not mains:
        status = "starting"
    else:
        cur = max(mains, key=lambda t: t.last_ts or 0)
        pend = cur.pending()
        if pend:
            status = "waiting" if pend[-1]["name"] in WAIT_TOOLS else "acting"
        elif cur.last_role == "assistant" and cur.last_stop == "end_turn":
            status = "done"
        else:
            status = "thinking"
    tools: dict[str, dict] = {}
    thoughts: dict[str, dict] = {}
    for t in mains:
        for i in t.order:
            if i in t.tools:
                tools[i] = t.tools[i]
        for r in t.reasoning:
            thoughts[r["mid"] or str(r["ts"])] = r
    log = sorted(thoughts.values(), key=lambda r: r["ts"] or 0)
    reasoning = log[-1] if log else None
    earlier = [{"kind": r["kind"], "text": r["text"][:700], "ts": r["ts"]} for r in reversed(log[-4:-1])]
    recent = sorted(tools.values(), key=lambda r: r["ts"] or 0)[-TOOL_HISTORY:]
    last = max((t.last_ts for t in mains), default=None)
    return {
        "status": status,
        "last_activity": last,
        "stale": bool(status in ("thinking", "acting") and last and time.time() - last > STALE_AFTER_S),
        "reasoning": {k: reasoning[k] for k in ("kind", "text", "ts")} if reasoning else None,
        "earlier": earlier,
        "tools": [dict(r) for r in reversed(recent)],
        "first_ts": min((t.first_ts for t in mains if t.first_ts), default=None),
        "sessions": len(mains),
        "model": next((t.model for t in reversed(mains) if t.model), None),
    }


# ── state assembly ──────────────────────────────────────────────────────


def downsample(points: list[tuple]) -> list[tuple]:
    if len(points) <= SPARK_POINTS:
        return points
    step = (len(points) - 1) / (SPARK_POINTS - 1)
    return [points[round(i * step)] for i in range(SPARK_POINTS)]


def build_civs(rows: dict[tuple[int, int], dict], map_players: list[dict], agent_pids: dict[int, int]) -> tuple[list, list]:
    by_pid: dict[int, list[dict]] = {}
    for (turn, pid), r in rows.items():
        by_pid.setdefault(pid, []).append(r)
    majors = set(by_pid)
    city_states = []
    for p in map_players:
        pid = p.get("pid")
        if not isinstance(pid, int):
            continue
        if p.get("csType"):
            city_states.append({
                "pid": pid, "name": nice_civ(p.get("civ")), "type": p["csType"],
                "color": CS_COLORS.get(p["csType"], "#8a8f96"),
            })
        elif pid < 62:
            majors.add(pid)
    civ_names = {p["pid"]: p.get("civ") for p in map_players if isinstance(p.get("pid"), int)}
    civs = []
    for i, pid in enumerate(sorted(majors)):
        hist = sorted(by_pid.get(pid, []), key=lambda r: r["turn"])
        last = hist[-1] if hist else {}
        pts = downsample([(r["turn"], num(r.get("score")), num(r.get("science")), num(r.get("culture"))) for r in hist])
        civs.append({
            "pid": pid,
            "civ": nice_civ(last.get("civ") or civ_names.get(pid)),
            "leader": nice_civ(last.get("leader")) if last.get("leader") else None,
            "color": MAJOR_COLORS[i % len(MAJOR_COLORS)],
            "agent": agent_pids.get(pid),
            "turn": last.get("turn"),
            "score": num(last.get("score")),
            "cities": num(last.get("cities")),
            "pop": num(last.get("pop")),
            "science": num(last.get("science")),
            "culture": num(last.get("culture")),
            "gold_per_turn": num(last.get("gold_per_turn")),
            "faith_per_turn": num(last.get("faith_per_turn")),
            "military": num(last.get("military")),
            "techs": num(last.get("techs_completed")),
            "civics": num(last.get("civics_completed")),
            "era": nice_civ(str(last.get("era") or "").removeprefix("ERA_")) if last.get("era") else None,
            "history": {
                "turn": [p[0] for p in pts], "score": [p[1] for p in pts],
                "science": [p[2] for p in pts], "culture": [p[3] for p in pts],
            },
        })
    civs.sort(key=lambda c: (-(c["score"] or -1), c["pid"]))
    for rank, c in enumerate(civs, 1):
        c["rank"] = rank
    return civs, city_states


def latest_reflections(rows: dict[tuple[int, int], dict], pid: int | None) -> dict | None:
    if pid is None:
        return None
    best = None
    for (turn, p), r in rows.items():
        refl = r.get("reflections")
        if p == pid and isinstance(refl, dict) and any(refl.get(k) for k in REFLECTION_KEYS):
            if best is None or turn > best[0]:
                best = (turn, refl)
    if not best:
        return None
    out = {"turn": best[0]}
    for k in REFLECTION_KEYS:
        v = best[1].get(k)
        out[k] = str(v).strip()[:1200] if v else None
    return out


def build_state(manifest: dict, tele: Telemetry, feeds: list[AgentFeed], prices: dict) -> dict:
    rows = tele.diary_rows()
    agents_cfg = manifest.get("agents") or []
    diary_agent_pids = sorted({pid for (_, pid), r in rows.items() if r.get("is_agent")})
    agent_pids: dict[int, int] = {}
    for i, a in enumerate(agents_cfg):
        pid = a.get("pid")
        if not isinstance(pid, int) and i < len(diary_agent_pids):
            pid = diary_agent_pids[i]
        if isinstance(pid, int):
            agent_pids.setdefault(pid, i)
    mp = tele.map_state()
    civs, city_states = build_civs(rows, (mp or {}).get("players", []), agent_pids)
    by_pid = {c["pid"]: c for c in civs}
    go = tele.game_over
    hb_done = bool(tele.heartbeat and tele.heartbeat.get("phase") == "finished")
    game_over = None
    if go:
        oc = go.get("outcome") or {}
        winner = nice_civ(oc.get("winner_civ"))
        win_pid = next((c["pid"] for c in civs if c["civ"].lower() == winner.lower()), None)
        game_over = {
            "turn": go.get("turn"), "ts": go.get("ts"), "winner_civ": winner,
            "winner_leader": nice_civ(oc.get("winner_leader")) if oc.get("winner_leader") else None,
            "victory_type": oc.get("victory_type"), "winner_pid": win_pid,
            "winner_agent": agent_pids.get(win_pid) if win_pid is not None else None,
        }
    elif hb_done:
        game_over = {"turn": tele.current_turn(), "ts": tele.heartbeat.get("ts"), "winner_civ": None,
                     "winner_leader": None, "victory_type": None, "winner_pid": None, "winner_agent": None}

    agents = []
    all_tx: list[Transcript] = []
    for i, a in enumerate(agents_cfg):
        feed = feeds[i]
        txs = feed.sync([str(p) for p in a.get("transcripts") or []])
        all_tx += txs
        act = agent_activity(txs, game_over is not None)
        pid = next((p for p, idx in agent_pids.items() if idx == i), None)
        civ = by_pid.get(pid) if pid is not None else None
        agents.append({
            "name": a.get("name") or f"Agent {i + 1}",
            "model": a.get("model") or act.pop("model"),
            "goal": a.get("goal"),
            "pid": pid,
            "civ": civ["civ"] if civ else None,
            "leader": civ["leader"] if civ else None,
            "color": civ["color"] if civ else MAJOR_COLORS[i % len(MAJOR_COLORS)],
            "rank": civ["rank"] if civ else None,
            "reflections": latest_reflections(rows, pid),
            "usage": usage_totals(txs, prices),
            **{k: v for k, v in act.items() if k != "model"},
        })

    started = parse_ts(manifest.get("started_at"))
    if started is None:
        firsts = [a["first_ts"] for a in agents if a.get("first_ts")]
        started = min(firsts) if firsts else tele.first_ts()
    ended = None
    if game_over:
        last = max((a["last_activity"] or 0 for a in agents), default=0) or None
        ended = game_over.get("ts") if (game_over.get("ts") or 0) > (started or 0) else last
    total = usage_totals(all_tx, prices)
    if mp:
        mp.pop("players", None)
        mp["city_states"] = city_states
    return {
        "v": STATE_VERSION,
        "generated_at": round(time.time(), 3),
        "demo": bool(manifest.get("demo")),
        "game": {
            "title": manifest.get("title") or "Civ 6 war room",
            "turn": tele.current_turn(),
            "started_at": started,
            "ended_at": ended,
            "game_over": game_over,
            "mcp_phase": (tele.heartbeat or {}).get("phase"),
        },
        "source": dict(tele.status),
        "cost": {k: total[k] for k in ("usd", "total", "input", "output", "cache_read", "cache_write_5m", "cache_write_1h", "unpriced_tokens", "requests")},
        "priced": bool(prices),
        "civs": civs,
        "agents": agents,
        "map": mp,
    }


# ── output ──────────────────────────────────────────────────────────────


MAP_RAW = frozenset({"terrain", "features", "rivers", "owners", "rev"})


def write_state(out: Path, state: dict, san: Sanitizer) -> None:
    clean = san.walk({k: v for k, v in state.items() if k != "map"})
    if state.get("map"):
        m = state["map"]
        clean["map"] = {k: (v if k in MAP_RAW else san.walk(v)) for k, v in m.items()}
    else:
        clean["map"] = None
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / f".state.{os.getpid()}.tmp"
    tmp.write_text(json.dumps(clean, separators=(",", ":"), ensure_ascii=False))
    os.replace(tmp, out / "state.json")


def publish(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for f in PAGE_FILES:
        shutil.copy2(PAGE_DIR / f, out / f)
    for d in PAGE_DIRS:
        if (PAGE_DIR / d).is_dir():
            shutil.copytree(PAGE_DIR / d, out / d, dirs_exist_ok=True)


def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    return data


def manifest_keys(m: dict) -> list[str]:
    keys = [m.get("game_key")] + [a.get("game_key") for a in m.get("agents") or []]
    return list(dict.fromkeys(k for k in keys if isinstance(k, str) and k and k != "auto"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--local-dir", type=Path, help="read civ6-mcp files from this folder instead of the game PC")
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--once", action="store_true", help="write state.json once and exit")
    ap.add_argument("--publish", action="store_true", help="copy the page files into --out")
    args = ap.parse_args(argv)

    out = args.out.expanduser()
    if args.publish:
        publish(out)
    manifest = load_manifest(args.manifest)
    m_mtime = args.manifest.stat().st_mtime
    source = LocalSource(args.local_dir.expanduser()) if args.local_dir else RemoteSource(manifest.get("civ6mcp_dir"))
    tele = Telemetry(source)
    feeds: list[AgentFeed] = []
    while True:
        t0 = time.time()
        try:
            mt = args.manifest.stat().st_mtime
            if mt != m_mtime:  # the runner may add a transcript when an agent switches account
                manifest, m_mtime = load_manifest(args.manifest), mt
        except (OSError, ValueError) as e:
            print(f"manifest not reloaded: {e}", file=sys.stderr)
        n = len(manifest.get("agents") or [])
        feeds = (feeds + [AgentFeed() for _ in range(n)])[:n]
        tele.poll(manifest_keys(manifest))
        state = build_state(manifest, tele, feeds, load_prices())
        write_state(out, state, sanitizer_for(manifest))
        if args.once:
            src = state["source"]
            print(f"wrote {out / 'state.json'}: turn {state['game']['turn']}, {len(state['civs'])} civs, "
                  f"{len(state['agents'])} agents, map {'yes' if state['map'] else 'no'}, "
                  f"source ok={src['ok']} folder={src['folder']} files={src['files']}"
                  + (f" error={src['error']}" if src["error"] else ""))
            return 0
        time.sleep(max(0.2, args.interval - (time.time() - t0)))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
