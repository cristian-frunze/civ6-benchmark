"""Copy a finished game's public files into results/<game-id>/ and print the numbers for its README.

    python3 tools/results.py --game-id g2-baseline [--shots 50,130,200,last]

Copies, from ~/.civ6-bench/runs/<game-id>/: archive/turns.jsonl, interventions.jsonl, the civ6-mcp diaries (gzipped)
and a few screenshots. Prints the totals, the cost split, cost and pace by 50-turn range, and the final standings.
Nothing private goes in: no account names, transcript paths or saves.
A hotseat game (tools/run_hotseat.py) gets its seat-turn rows, per-round stats and the seats' diary instead.
"""

import argparse
import gzip
import json
import shutil
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def price(run: Path) -> dict:
    """$/MTok for the game's model (warroom/prices.json), with 1-hour cache writes as the runners use them."""
    model = "claude-opus-5-5"
    if (run / "game.json").exists():
        model = (json.loads((run / "game.json").read_text()).get("agents") or [{}])[0].get("model") or model
    p = json.loads((REPO / "warroom" / "prices.json").read_text())[model]
    return {"output": p["output"], "cache_read": p["cache_read"], "cache_write": p["cache_write_1h"], "input": p["input"]}


def gz(src: Path, dst: Path) -> None:
    with open(src, "rb") as f, open(dst, "wb") as raw, \
            gzip.GzipFile(filename="", fileobj=raw, mode="wb", compresslevel=9, mtime=0) as out:  # byte-stable
        shutil.copyfileobj(f, out)


def hotseat(run: Path, out: Path) -> None:
    """A hotseat game (tools/run_hotseat.py): per seat-turn rows without account names, the per-round stats of every
    civ, and the coordinator's diary (each seat's reflections), then totals per seat and the final standings."""
    rows = [json.loads(ln) for ln in open(run / "turns.jsonl")]
    with open(out / "turns.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps({k: v for k, v in r.items() if k != "account"}) + "\n")
    shutil.copy2(run / "rounds.jsonl", out / "rounds.jsonl")
    if (run / "interventions.jsonl").exists():
        shutil.copy2(run / "interventions.jsonl", out / "interventions.jsonl")
    for d in sorted((run / "telemetry").glob("diary_*.jsonl")):
        gz(d, out / "diary.jsonl.gz")
    total = sum(r.get("usd") or 0 for r in rows)
    wall = (max(r["end"] for r in rows) - min(r["start"] for r in rows)) / 3600
    print(f"seat turns {len(rows)}, last turn {rows[-1]['turn']}, wall {wall:.2f} h, usd {total:.2f}")
    for seat in dict.fromkeys(r["seat"] for r in rows):
        xs = [r for r in rows if r["seat"] == seat]
        print(f"  {seat} ({xs[0]['leader']}): {len({r['turn'] for r in xs})} turns, ${sum(r.get('usd') or 0 for r in xs):.2f}, "
              f"median {statistics.median(r['seconds'] for r in xs):.0f} s, {sum(r.get('requests') or 0 for r in xs)} requests, "
              f"{sum(1 for r in xs if r.get('try', 1) > 1)} retries")
    print("cost split: " + ", ".join(f"{k} ${sum(r.get(k) or 0 for r in rows) * p / 1e6:.2f}" for k, p in price(run).items()))
    last = [json.loads(ln) for ln in open(run / "rounds.jsonl")][-1]
    print(f"standings at turn {last.get('turn')} (civ, score, cities, science, techs, civics, military, agent), "
          f"winning team {last.get('winning_team')}:")
    for p in sorted(last["players"], key=lambda p: -p["score"]):
        print(f"  {p['civ']} {p['score']} {p['cities']} {round(p['science'])} {p['techs']} {p['civics']} {p['military']} {p['human']}")
    print(f"copied to {out.relative_to(REPO)}: " + ", ".join(sorted(p.name for p in out.rglob('*') if p.is_file())))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-id", required=True)
    ap.add_argument("--runtime-dir", default="~/.civ6-bench/runs")
    ap.add_argument("--shots", default="50,130,200,last")
    a = ap.parse_args()
    run = Path(a.runtime_dir).expanduser() / a.game_id
    arch = run / "archive"
    out = REPO / "results" / a.game_id
    (out / "shots").mkdir(parents=True, exist_ok=True)
    if (run / "game.json").exists() and json.loads((run / "game.json").read_text()).get("mode") == "hotseat":
        (out / "shots").rmdir()
        return hotseat(run, out)

    turns = [json.loads(ln) for ln in open(arch / "turns.jsonl")]
    shutil.copy2(arch / "turns.jsonl", out / "turns.jsonl")
    if (run / "interventions.jsonl").exists():
        shutil.copy2(run / "interventions.jsonl", out / "interventions.jsonl")
    diaries = sorted((arch / "civ6mcp").glob(f"diary_*_{a.game_id}*.jsonl"))
    for d in diaries:
        gz(d, out / ("diary_cities.jsonl.gz" if d.stem.endswith("_cities") else "diary.jsonl.gz"))
    shots = sorted((arch / "shots").glob("T*.jpg"))
    for want in a.shots.split(","):
        pick = shots[-1] if want == "last" else next((s for s in shots if int(s.stem[1:]) >= int(want)), None)
        if pick:
            shutil.copy2(pick, out / "shots" / pick.name)

    S = lambda k: sum(t.get(k) or 0 for t in turns)  # noqa: E731
    secs = [t["end"] - t["start"] for t in turns if t.get("end") and t.get("start")]
    wall = (max(t["end"] for t in turns) - min(t["start"] for t in turns)) / 3600
    print(f"turns {len(turns)} (last {turns[-1]['turn']}), wall {wall:.2f} h, median {statistics.median(secs):.0f} s/turn")
    print(f"usd {S('usd'):.2f}; requests {S('requests')}; tool calls {S('tool_calls')} ({S('tool_errors')} errors)")
    print(f"tokens: output {S('output'):,}, cache read {S('cache_read'):,}, cache write {S('cache_write'):,}, input {S('input'):,}")
    print("cost split: " + ", ".join(f"{k} ${S(k) * p / 1e6:.2f}" for k, p in price(run).items()))
    last = turns[-1]["turn"]
    for lo in range(1, last + 1, 50):
        hi = min(lo + 49, last)
        xs = [t for t in turns if lo <= t["turn"] <= hi]
        if xs:
            med = statistics.median(t["end"] - t["start"] for t in xs)
            print(f"  turns {lo}-{hi}: ${sum(t['usd'] for t in xs):.2f}, median {med:.0f} s, "
                  f"{sum(t['requests'] for t in xs) / len(xs):.1f} requests/turn")
    main_diary = next((d for d in diaries if not d.stem.endswith("_cities")), None)
    if main_diary:
        rows = list({(r.get("turn"), r.get("civ")): r for r in map(json.loads, open(main_diary))}.values())  # last row per civ and turn
        top = max(r.get("turn", 0) for r in rows)
        print(f"standings at turn {top} (civ, score, cities, science, techs, civics, military, agent):")
        for r in sorted((r for r in rows if r.get("turn") == top), key=lambda r: -r.get("score", 0)):
            print(f"  {r.get('civ')} {r.get('score')} {r.get('cities')} {round(r.get('science') or 0)} "
                  f"{r.get('techs_completed')} {r.get('civics_completed')} {r.get('military')} {r.get('is_agent')}")
    print(f"copied to {out.relative_to(REPO)}: " + ", ".join(sorted(p.name for p in out.rglob('*') if p.is_file())))


if __name__ == "__main__":
    main()
