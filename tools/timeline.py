"""Per-turn record of what the agent thought and did, built from a run's archive (tools/archive.py).

Joins every Claude Code session transcript (thinking, messages, tool calls, tool results, token usage) with
civ6-mcp's tool log (the game turn and timing of each call) and diary (per-turn stats for every civ). Writes
into <run dir>/archive/:

  timeline.jsonl   every agent event in order: {ts, turn, session, kind, ...}
                     thinking {text} | text {text} | tool_call {tool, input, id} | tool_result {tool, id, is_error, result}
  turns.jsonl      one row per turn: start, seconds, API requests, tokens and API-equivalent USD, tool calls and
                   errors, thinking chars, the agent's end-of-turn reflections, its diary row (score, yields, ...)
  timeline.md      the same, to read: per turn, the reasoning, the actions and their results

A transcript event belongs to the turn of the next call civ6-mcp logged, since civ6-mcp stamps a call when it
finishes. The game PC's clock is aligned to this machine's on the end_turn calls, which both sides record.
tools/archive.py rebuilds these files after each sync, so they stay current during a game.

    python3 tools/timeline.py --run-dir ~/.civ6-bench/runs/g1-standard
"""

from __future__ import annotations

import argparse
import ast
import bisect
import json
import statistics
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESULT_CHARS = 6000  # per tool result in timeline.jsonl; civ6-mcp's log keeps every result in full
MD_RESULT_CHARS = 600
PREFIX = "mcp__civ6__"


def ts_of(s: str | None) -> float | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() if s else None
    except ValueError:
        return None


def jsonl(path: Path) -> list[dict]:
    rows = []
    if path.exists():
        for line in path.open(encoding="utf-8", errors="replace"):
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass  # a line still being written
    return rows


def result_text(content) -> str:
    if isinstance(content, list):
        content = "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
    if not isinstance(content, str):
        return ""
    try:  # civ6-mcp's tools return {"result": "<text>"}
        d = json.loads(content)
        if isinstance(d, dict) and set(d) == {"result"} and isinstance(d["result"], str):
            return d["result"]
    except ValueError:
        pass
    return content


def prices() -> dict:
    try:
        return {k: v for k, v in json.loads((REPO / "warroom" / "prices.json").read_text()).items() if isinstance(v, dict)}
    except (OSError, ValueError):
        return {}


def usd(model: str, u: dict, table: dict) -> float | None:
    p = table.get(model) or next((table[k] for k in sorted(table, key=len, reverse=True) if model.startswith(k)), None)
    if not p:
        return None
    cc = u.get("cache_creation") or {}
    cw1 = cc.get("ephemeral_1h_input_tokens") or 0
    cw5 = cc.get("ephemeral_5m_input_tokens") if cc else (u.get("cache_creation_input_tokens") or 0)
    return ((u.get("input_tokens") or 0) * p.get("input", 0) + (u.get("output_tokens") or 0) * p.get("output", 0)
            + (u.get("cache_read_input_tokens") or 0) * p.get("cache_read", 0)
            + (cw5 or 0) * p.get("cache_write_5m", 0) + cw1 * p.get("cache_write_1h", 0)) / 1e6


def transcript_events(path: Path, session: str, table: dict) -> list[dict]:
    """Thinking, text, tool calls, tool results and per-request usage from one Claude Code transcript."""
    out, names, seen = [], {}, set()
    for e in jsonl(path):
        if e.get("type") not in ("assistant", "user") or e.get("isSidechain"):
            continue
        t = ts_of(e.get("timestamp"))
        msg = e.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list) or t is None:
            continue
        base = {"ts": t, "session": session}
        if e["type"] == "assistant" and (mid := msg.get("id")) and mid not in seen and isinstance(msg.get("usage"), dict) \
                and msg.get("model") != "<synthetic>":
            seen.add(mid)  # one API response is spread over several rows that repeat its usage
            u = msg["usage"]
            out.append(base | {"kind": "usage", "model": msg.get("model"), "input": u.get("input_tokens") or 0,
                               "output": u.get("output_tokens") or 0, "cache_read": u.get("cache_read_input_tokens") or 0,
                               "cache_write": u.get("cache_creation_input_tokens") or 0, "usd": usd(msg.get("model") or "", u, table)})
        for b in content:
            kind = b.get("type")
            if kind == "thinking" and b.get("thinking"):
                out.append(base | {"kind": "thinking", "text": b["thinking"]})
            elif kind == "text" and b.get("text", "").strip():
                out.append(base | {"kind": "text", "text": b["text"]})
            elif kind == "tool_use":
                tool = b.get("name", "").removeprefix(PREFIX)
                names[b.get("id")] = tool
                out.append(base | {"kind": "tool_call", "tool": tool, "id": b.get("id"), "input": b.get("input")})
            elif kind == "tool_result":
                out.append(base | {"kind": "tool_result", "tool": names.get(b.get("tool_use_id"), "?"), "id": b.get("tool_use_id"),
                                   "is_error": bool(b.get("is_error")), "result": result_text(b.get("content"))[:RESULT_CHARS]})
    return out


class Turns:
    """Maps a time on this machine to the game turn, from civ6-mcp's log of finished calls."""

    def __init__(self, log: list[dict], events: list[dict]):
        rows = sorted((r["ts"], int(r.get("turn") or 0), r.get("tool")) for r in log if isinstance(r.get("ts"), (int, float)))
        ends_log = [ts for ts, _, tool in rows if tool == "end_turn"]
        ends_tx = [e["ts"] for e in events if e["kind"] == "tool_result" and e["tool"] == "end_turn"]
        pairs = [a - b for a, b in zip(ends_tx, ends_log)]
        self.offset = statistics.median(pairs) if pairs else 0.0
        self.ts = [ts + self.offset for ts, _, _ in rows]
        self.turn = [turn for _, turn, _ in rows]
        self.tool = [tool for _, _, tool in rows]

    def at(self, t: float) -> int:
        if not self.ts:
            return 0
        i = bisect.bisect_left(self.ts, t - 0.5)
        if i < len(self.ts):
            return self.turn[i]
        return self.turn[-1] + (1 if self.tool[-1] == "end_turn" else 0)  # after the last logged call


def reflections(inp) -> dict:
    keys = ("tactical", "strategic", "tooling", "planning", "hypothesis")
    return {k: inp[k] for k in keys if isinstance(inp, dict) and inp.get(k)}


def diary_rows(civdir: Path) -> dict[int, dict]:
    rows = {}
    for p in civdir.glob("diary_*.jsonl"):
        if p.name.endswith("_cities.jsonl"):
            continue
        for r in jsonl(p):
            if str(r.get("is_agent")).lower() == "true":
                try:
                    turn = int(r.get("turn"))
                except (TypeError, ValueError):
                    continue
                r = dict(r)
                if isinstance(r.get("reflections"), str):
                    try:
                        r["reflections"] = ast.literal_eval(r["reflections"])
                    except (ValueError, SyntaxError):
                        pass
                rows[turn] = r
    return rows


DIARY_KEYS = ("score", "cities", "pop", "science", "culture", "gold", "gold_per_turn", "faith", "military", "units_total",
              "techs_completed", "civics_completed", "exploration_pct", "era", "government")


def build(run_dir: Path) -> dict:
    arch = run_dir / "archive"
    table = prices()
    events: list[dict] = []
    for p in sorted((arch / "transcripts").glob("*.jsonl")):
        events += transcript_events(p, p.stem.split("-", 1)[0], table)
    events.sort(key=lambda e: e["ts"])
    log = [r for p in (arch / "civ6mcp").glob("log_*.jsonl") for r in jsonl(p) if r.get("type") == "tool_call"]
    turns = Turns(log, events)
    call_turn = {}
    for e in events:
        if e["kind"] == "tool_result" and e["id"] in call_turn:
            e["turn"] = call_turn[e["id"]]  # a result belongs with its call, even end_turn's
        else:
            e["turn"] = turns.at(e["ts"])
        if e["kind"] == "tool_call":
            call_turn[e["id"]] = e["turn"]

    diary = diary_rows(arch / "civ6mcp")
    per: dict[int, dict] = {}
    for e in events:
        t = per.setdefault(e["turn"], {"turn": e["turn"], "start": e["ts"], "end": e["ts"], "requests": 0, "input": 0,
                                       "output": 0, "cache_read": 0, "cache_write": 0, "usd": 0.0, "tool_calls": 0,
                                       "tool_errors": 0, "thinking_chars": 0, "sessions": []})
        t["end"] = e["ts"]
        if e["session"] not in t["sessions"]:
            t["sessions"].append(e["session"])
        k = e["kind"]
        if k == "usage":
            t["requests"] += 1
            for f in ("input", "output", "cache_read", "cache_write"):
                t[f] += e[f]
            t["usd"] += e["usd"] or 0
        elif k == "thinking":
            t["thinking_chars"] += len(e["text"])
        elif k == "tool_call":
            t["tool_calls"] += 1
            if e["tool"] == "end_turn":
                t["reflections"] = reflections(e["input"])
        elif k == "tool_result" and e["is_error"]:
            t["tool_errors"] += 1
    rows = []
    for n in sorted(per):
        t = per[n]
        t["seconds"] = round(t["end"] - t["start"], 1)
        t["usd"] = round(t["usd"], 4)
        if n in diary:
            t["diary"] = {k: diary[n].get(k) for k in DIARY_KEYS}
            t.setdefault("reflections", diary[n].get("reflections") if isinstance(diary[n].get("reflections"), dict) else {})
        rows.append(t)

    write_jsonl(arch / "timeline.jsonl", events)
    write_jsonl(arch / "turns.jsonl", rows)
    (arch / "timeline.md").write_text(markdown(run_dir, events, rows, turns.offset))
    return {"events": len(events), "turns": len(rows), "clock_offset_s": round(turns.offset, 2)}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(path)


def clip(s: str, n: int) -> str:
    s = s.strip()
    return s if len(s) <= n else s[:n] + f" ... [{len(s) - n} more chars]"


def markdown(run_dir: Path, events: list[dict], rows: list[dict], offset: float) -> str:
    try:
        m = json.loads((run_dir / "game.json").read_text())
    except (OSError, ValueError):
        m = {}
    total = sum(r["usd"] for r in rows)
    out = [f"# {m.get('title', run_dir.name)}: turn by turn", "",
           f"{m.get('civ', '')}, {m.get('difficulty', '')}, {m.get('map', '')}, {m.get('speed', '')} speed. "
           f"{len(rows)} turns, ${total:.2f} API-equivalent. Game PC clock offset {offset:+.1f} s.", ""]
    by_turn: dict[int, list[dict]] = {}
    for e in events:
        by_turn.setdefault(e["turn"], []).append(e)
    for r in rows:
        d = r.get("diary") or {}
        stats = ", ".join(f"{k} {d[k]}" for k in ("score", "cities", "pop", "science", "culture", "gold") if d.get(k) is not None)
        out += [f"## Turn {r['turn']}", "",
                f"{r['seconds']:.0f} s, {r['requests']} API requests, {r['output']:,} output tokens, ${r['usd']:.2f}, "
                f"{r['tool_calls']} tool calls ({r['tool_errors']} errors)." + (f" Diary: {stats}." if stats else ""), ""]
        for e in by_turn.get(r["turn"], []):
            k = e["kind"]
            if k == "thinking":
                out += ["> " + line for line in e["text"].strip().splitlines()] + [""]
            elif k == "text":
                out += [e["text"].strip(), ""]
            elif k == "tool_call":
                out += [f"- **{e['tool']}** `{json.dumps(e['input'], ensure_ascii=False)[:400]}`"]
            elif k == "tool_result":
                body = clip(e["result"], MD_RESULT_CHARS).replace("\n", "\n    ")
                out += [f"  - {'ERROR ' if e['is_error'] else ''}{e['tool']} -> {body}", ""]
        if r.get("reflections"):
            out += ["**Reflections:**", ""] + [f"- {k}: {v}" for k, v in r["reflections"].items()] + [""]
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True, type=lambda s: Path(s).expanduser())
    print(json.dumps(build(ap.parse_args().run_dir)))


if __name__ == "__main__":
    main()
