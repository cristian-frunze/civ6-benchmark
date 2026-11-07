"""Copy a finished single-player game's public files into results/<game-id>/ and print the numbers for its README.

    python3 tools/results.py --game-id g2-baseline [--shots 50,130,200,last]

Copies, from ~/.civ6-bench/runs/<game-id>/: archive/turns.jsonl, interventions.jsonl, the civ6-mcp diaries (gzipped)
and a few screenshots. Prints the totals, the cost split, cost and pace by 50-turn range, and the final standings.
Nothing private goes in: no account names, transcript paths or saves.
"""

import argparse
import gzip
import json
import shutil
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PRICE = {"input": 4, "output": 20, "cache_read": 0.2, "cache_write": 8}  # Opus 5.5 $/MTok, 1-hour cache writes


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

    turns = [json.loads(ln) for ln in open(arch / "turns.jsonl")]
    shutil.copy2(arch / "turns.jsonl", out / "turns.jsonl")
    if (run / "interventions.jsonl").exists():
        shutil.copy2(run / "interventions.jsonl", out / "interventions.jsonl")
    diaries = sorted((arch / "civ6mcp").glob(f"diary_*_{a.game_id}*.jsonl"))
    for d in diaries:
        name = "diary_cities.jsonl.gz" if d.stem.endswith("_cities") else "diary.jsonl.gz"
        with open(d, "rb") as src, open(out / name, "wb") as raw, \
                gzip.GzipFile(filename="", fileobj=raw, mode="wb", compresslevel=9, mtime=0) as dst:  # byte-stable
            shutil.copyfileobj(src, dst)
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
    print("cost split: " + ", ".join(f"{k} ${S(k) * p / 1e6:.2f}" for k, p in PRICE.items()))
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
