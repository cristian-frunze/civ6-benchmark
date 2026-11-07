"""Build one HTML page comparing the benchmark games: result, cost, pace, and how far the agent led the AI.

    python3 tools/report.py --out ~/tailscale-share/civ6-results/index.html \
        [--game g1-standard] [--game g2-baseline=~/.civ6-bench/runs/g2-baseline] ...

Each --game is a results/<id>/ folder (turns.jsonl, diary.jsonl.gz) or, with =<dir>, a live run directory
(archive/turns.jsonl, archive/civ6mcp/diary_*.jsonl). Without --game it uses every folder in results/. The page is
self-contained (inline data, SVG drawn in the browser, no external scripts).
"""

import argparse
import gzip
import html
import json
import re
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PRICE = {"input": 4, "output": 20, "cache_read": 0.2, "cache_write": 8}
LABELS = {"g1-standard": "Game 1, playbook", "g2-baseline": "Game 2, rules only", "g3-science": "Game 3, Science goal",
          "g4-domination": "Game 4, Domination goal"}


def _rows(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def load(gid: str, src: Path) -> dict:
    turns_p = src / "turns.jsonl" if (src / "turns.jsonl").exists() else src / "archive" / "turns.jsonl"
    diary_p = src / "diary.jsonl.gz"
    if not diary_p.exists():
        diary_p = next((p for p in sorted((src / "archive" / "civ6mcp").glob("diary_*.jsonl"))
                        if not p.stem.endswith("_cities")), None)
    turns = {}
    for t in _rows(turns_p):
        turns[t["turn"]] = t  # a replayed turn keeps its last row
    turns = [turns[k] for k in sorted(turns)]
    diary: dict[tuple, dict] = {}
    for r in _rows(diary_p) if diary_p else []:
        diary[(r.get("turn"), r.get("civ"))] = r
    by_turn: dict[int, list] = {}
    for (turn, _), r in diary.items():
        by_turn.setdefault(turn, []).append(r)

    readme = src / "README.md"
    title, result = LABELS.get(gid, gid), "in progress"
    if readme.exists():
        text = readme.read_text()
        title = LABELS.get(gid) or text.splitlines()[0].lstrip("# ").strip() or gid
        hit = re.search(r"\*\*Result: ([^*]+?)\.?\*\*", text)
        result = hit.group(1) if hit else "finished"
    cum, cost_series, lead_series, sci_series = 0.0, [], [], []
    for t in turns:
        cum += t.get("usd") or 0
        cost_series.append([t["turn"], round(cum, 2)])
    for turn in sorted(by_turn):
        rows = by_turn[turn]
        me = next((r for r in rows if r.get("is_agent")), None)
        ais = [r for r in rows if not r.get("is_agent")]
        if me and ais:
            lead_series.append([turn, (me.get("techs_completed") or 0) - max(r.get("techs_completed") or 0 for r in ais)])
            sci_series.append([turn, round((me.get("science") or 0) / max(max(r.get("science") or 0 for r in ais), 0.1), 2)])
    last = by_turn.get(max(by_turn)) if by_turn else []
    standings = sorted(({"civ": r.get("civ"), "agent": bool(r.get("is_agent")), "score": r.get("score"),
                         "cities": r.get("cities"), "science": round(r.get("science") or 0),
                         "techs": r.get("techs_completed"), "civics": r.get("civics_completed"),
                         "military": r.get("military")} for r in last or []), key=lambda r: -(r["score"] or 0))
    S = lambda k: sum(t.get(k) or 0 for t in turns)  # noqa: E731
    secs = [t["end"] - t["start"] for t in turns if t.get("end") and t.get("start")]
    wall = (max(t["end"] for t in turns) - min(t["start"] for t in turns)) / 3600 if turns else 0
    return {
        "id": gid, "title": title, "result": result, "turns": len(turns),
        "last_turn": lead_series[-1][0] if lead_series else (turns[-1]["turn"] if turns else 0),
        "usd": round(S("usd"), 2), "usd_per_turn": round(S("usd") / max(len(turns), 1), 3),
        "median_s": round(statistics.median(secs)) if secs else 0, "wall_h": round(wall, 1),
        "requests": S("requests"), "tool_calls": S("tool_calls"), "tool_errors": S("tool_errors"),
        "output": S("output"), "cache_read": S("cache_read"), "cache_write": S("cache_write"), "input": S("input"),
        "split": {k: round(S(k) * p / 1e6, 2) for k, p in PRICE.items()},
        "cost": cost_series, "lead": lead_series, "sci": sci_series, "standings": standings,
    }


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Civ 6 Benchmark</title>
<style>
:root{color-scheme:light;--bg:#f6f6f4;--surface:#fcfcfb;--line:#e4e3df;--grid:#ecebe7;--ink:#0b0b0b;--ink2:#52514e;--ink3:#7a7974;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--zero:#b9b8b2}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#121211;--surface:#1a1a19;--line:#2c2c2a;
--grid:#262624;--ink:#f0efec;--ink2:#c3c2b7;--ink3:#8f8e88;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--zero:#55544f}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#121211;--surface:#1a1a19;--line:#2c2c2a;--grid:#262624;--ink:#f0efec;--ink2:#c3c2b7;
--ink3:#8f8e88;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--zero:#55544f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 16px 60px}h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:34px 0 4px}
.sub{color:var(--ink2);margin:0 0 18px}.note{color:var(--ink3);font-size:13px;margin:4px 0 10px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}
th,td{padding:6px 10px;text-align:right;border-bottom:1px solid var(--grid);white-space:nowrap}th{color:var(--ink2);font-weight:600}
td:first-child,th:first-child{text-align:left}tr:last-child td{border-bottom:0}
.sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:7px;vertical-align:baseline}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--ink2);margin:2px 0 8px}
.chart{position:relative}.chart svg{display:block;width:100%;height:auto}
.tip{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:6px 9px;
font-size:12.5px;box-shadow:0 2px 10px rgba(0,0,0,.12);display:none;white-space:nowrap}
.tip b{font-weight:600}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:760px){.grid2{grid-template-columns:1fr}}
.agent{font-weight:600}
</style></head><body><main>
<h1>Civ 6 benchmark: Opus 5.5</h1>
<p class="sub">Claude Opus 5.5 (high effort) against the game's built-in AI, base game, Prince, standard Pangaea, same seed and civs. Games 1-2 at Quick speed (330-turn limit), later games at Online speed (250). Costs are API-equivalent at list prices.</p>
<div class="card"><table id="summary"></table></div>
<h2>Cumulative API-equivalent cost</h2><p class="note">Dollars spent by the end of each turn.</p>
<div class="card"><div class="legend" id="lg-cost"></div><div class="chart" id="c-cost"></div></div>
<h2>Tech lead over the best AI civ</h2><p class="note">Techs Opus had researched minus the most any AI civ had, per turn. Above zero, Opus leads.</p>
<div class="card"><div class="legend" id="lg-lead"></div><div class="chart" id="c-lead"></div></div>
<h2>Where the money goes</h2><p class="note">API-equivalent dollars by token type. Every request rereads the whole conversation from cache.</p>
<div class="card"><table id="split"></table></div>
<h2>Final standings</h2><div class="grid2" id="standings"></div>
<p class="note" style="margin-top:28px">Data: __SOURCES__. Generated by tools/report.py.</p>
</main>
<script>
const G = __DATA__;
const COL = ["var(--s1)","var(--s2)","var(--s3)"];
const fmt = (n, d=0) => Number(n).toLocaleString("en-US", {minimumFractionDigits:d, maximumFractionDigits:d});
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function sw(i){return `<span class="sw" style="background:${COL[i]}"></span>`}
document.getElementById("summary").innerHTML =
 `<tr><th>Game</th><th>Result</th><th>Turns</th><th>Cost</th><th>$ / turn</th><th>Median s / turn</th><th>Hours</th><th>Requests</th><th>Tool calls</th></tr>` +
 G.map((g,i)=>`<tr><td>${sw(i)}${esc(g.title)}</td><td style="text-align:left">${esc(g.result)}</td><td>${g.last_turn}</td><td>$${fmt(g.usd,2)}</td><td>$${fmt(g.usd_per_turn,2)}</td><td>${g.median_s}</td><td>${g.wall_h}</td><td>${fmt(g.requests)}</td><td>${fmt(g.tool_calls)}</td></tr>`).join("");
document.getElementById("split").innerHTML =
 `<tr><th>Game</th><th>Cache read</th><th>Cache write</th><th>Output</th><th>Input</th></tr>` +
 G.map((g,i)=>`<tr><td>${sw(i)}${esc(g.title)}</td><td>$${fmt(g.split.cache_read,2)}</td><td>$${fmt(g.split.cache_write,2)}</td><td>$${fmt(g.split.output,2)}</td><td>$${fmt(g.split.input,2)}</td></tr>`).join("");
document.getElementById("standings").innerHTML = G.map((g,i)=>`<div class="card"><div style="font-weight:600;margin-bottom:6px">${sw(i)}${esc(g.title)}, turn ${g.last_turn}</div><table>
 <tr><th>Civ</th><th>Score</th><th>Cities</th><th>Sci</th><th>Techs</th><th>Military</th></tr>` +
 g.standings.map(r=>`<tr class="${r.agent?'agent':''}"><td>${esc(r.civ)}${r.agent?' (Opus)':''}</td><td>${r.score}</td><td>${r.cities}</td><td>${r.science}</td><td>${r.techs}</td><td>${r.military}</td></tr>`).join("") + `</table></div>`).join("");

function legend(id){document.getElementById(id).innerHTML = G.map((g,i)=>`<span>${sw(i)}${esc(g.title)}</span>`).join("")}
function line(id, key, yfmt, zero){
  const el = document.getElementById(id), W = Math.max(300, Math.round(el.clientWidth)), H = W < 600 ? 230 : 300, m = {l:44, r:46, t:12, b:28};
  const all = G.flatMap(g => g[key]); if (!all.length) return;
  const xmax = Math.max(...all.map(p=>p[0])), ys = all.map(p=>p[1]);
  let ymin = Math.min(0, ...ys), ymax = Math.max(...ys); const pad = (ymax - ymin) * .06 || 1; ymax += pad; if (ymin < 0) ymin -= pad;
  const X = x => m.l + (x - 1) / Math.max(xmax - 1, 1) * (W - m.l - m.r), Y = y => m.t + (1 - (y - ymin) / (ymax - ymin)) * (H - m.t - m.b);
  const ticks = n => { const s = (ymax - ymin) / n, p = Math.pow(10, Math.floor(Math.log10(s))), st = [1,2,5,10].map(k=>k*p).find(k=>k>=s);
    const out = []; for (let v = Math.ceil(ymin/st)*st; v <= ymax; v += st) out.push(+v.toFixed(6)); return out; };
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${key} by turn">`;
  for (const v of ticks(5)) s += `<line x1="${m.l}" x2="${W-m.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="${v===0&&zero?'var(--zero)':'var(--grid)'}" stroke-width="1"/><text x="${m.l-8}" y="${Y(v)+4}" text-anchor="end" font-size="12" fill="var(--ink3)">${yfmt(v)}</text>`;
  const xs = W < 600 ? 100 : 50;
  for (let x = xs; x <= xmax; x += xs) s += `<text x="${X(x)}" y="${H-8}" text-anchor="middle" font-size="12" fill="var(--ink3)">T${x}</text>`;
  G.forEach((g,i) => { const p = g[key]; if (!p.length) return;
    s += `<path d="${p.map((q,j)=>(j?'L':'M')+X(q[0]).toFixed(1)+','+Y(q[1]).toFixed(1)).join('')}" fill="none" stroke="${COL[i]}" stroke-width="2" stroke-linejoin="round"/>`;
    const e = p[p.length-1]; s += `<circle cx="${X(e[0])}" cy="${Y(e[1])}" r="4" fill="${COL[i]}" stroke="var(--surface)" stroke-width="2"/>
    <text x="${X(e[0])+8}" y="${Y(e[1])+4}" font-size="12" fill="var(--ink2)">${yfmt(e[1])}</text>`; });
  s += `<line id="${id}-x" y1="${m.t}" y2="${H-m.b}" stroke="var(--ink3)" stroke-width="1" visibility="hidden"/>`;
  s += G.map((g,i)=>`<circle id="${id}-d${i}" r="4" fill="${COL[i]}" stroke="var(--surface)" stroke-width="2" visibility="hidden"/>`).join("");
  s += `<rect x="${m.l}" y="0" width="${W-m.l-m.r}" height="${H}" fill="transparent"/></svg><div class="tip"></div>`;
  el.innerHTML = s; const svg = el.querySelector("svg"), tip = el.querySelector(".tip"), vx = document.getElementById(id+"-x");
  svg.addEventListener("pointermove", ev => { const r = svg.getBoundingClientRect(), sx = (ev.clientX - r.left) * W / r.width;
    const t = Math.round(1 + (sx - m.l) / (W - m.l - m.r) * (xmax - 1)); if (t < 1 || t > xmax) return;
    vx.setAttribute("x1", X(t)); vx.setAttribute("x2", X(t)); vx.setAttribute("visibility", "visible");
    let rows = ""; G.forEach((g,i) => { const p = g[key].find(q=>q[0]===t), d = document.getElementById(id+"-d"+i);
      if (p) { d.setAttribute("cx", X(t)); d.setAttribute("cy", Y(p[1])); d.setAttribute("visibility","visible"); rows += `<div>${sw(i)}${esc(g.title)}: <b>${yfmt(p[1])}</b></div>`; }
      else d.setAttribute("visibility","hidden"); });
    tip.innerHTML = `<div style="color:var(--ink3)">Turn ${t}</div>` + rows; tip.style.display = "block";
    const px = (ev.clientX - r.left), w = tip.offsetWidth; tip.style.left = (px + 14 + w > r.width ? px - w - 14 : px + 14) + "px"; tip.style.top = "8px"; });
  svg.addEventListener("pointerleave", () => { tip.style.display = "none"; vx.setAttribute("visibility","hidden");
    G.forEach((g,i)=>document.getElementById(id+"-d"+i).setAttribute("visibility","hidden")); });
}
legend("lg-cost"); legend("lg-lead");
function draw(){ line("c-cost", "cost", v => "$" + fmt(v, v < 10 && v % 1 ? 1 : 0)); line("c-lead", "lead", v => (v > 0 ? "+" : "") + fmt(v), true); }
draw(); let rz; addEventListener("resize", () => { clearTimeout(rz); rz = setTimeout(draw, 150); });
</script></body></html>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--game", action="append", default=[], help="<id> (results/<id>) or <id>=<run dir>")
    a = ap.parse_args()
    specs = a.game or sorted(p.name for p in (REPO / "results").iterdir() if p.is_dir())
    games = []
    for spec in specs:
        gid, _, src = spec.partition("=")
        games.append(load(gid, Path(src).expanduser() if src else REPO / "results" / gid))
    out = Path(a.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    sources = ", ".join(html.escape(g["id"]) for g in games)
    out.write_text(PAGE.replace("__DATA__", json.dumps(games).replace("</", "<\\/")).replace("__SOURCES__", sources))
    for g in games:
        print(f"{g['id']}: turn {g['last_turn']}, ${g['usd']}, {len(g['lead'])} diary turns")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
