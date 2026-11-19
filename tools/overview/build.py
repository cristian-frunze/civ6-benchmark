"""Build the civ6-benchmarks share page: ladder, tech-lead small multiples, cost dot plot, ledger.

    python3 tools/overview/build.py [--out ~/tailscale-share/civ6-benchmarks/index.html]
"""

import argparse
import html
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import report  # noqa: E402

GH = "https://github.com/cristian-frunze/civ6-benchmark/tree/main/results/"
LEVELS = [("Prince", "level 4 of 8"), ("King", "level 5"), ("Emperor", "level 6"), ("Deity", "level 8, the hardest")]
MODELS = [  # key, name, detail, css color var
    ("opus", "Opus 5.5", "high effort", "opus"),
    ("f52", "Fable 5.2", "high effort", "f52"),
    ("son", "Sonnet 5.5", "high effort", "son"),
    ("f51", "Fable 5.1", "high effort", "f51"),
    ("opusmed", "Opus 5.5", "medium effort", "opus"),
]
# Science goal, Online speed, same map and start. (id, model, level, won, winner if lost, note)
LADDER = [
    ("g3-science", "opus", "Prince", True, None, "First game at Online speed, on the early harness"),
    ("g5-deity-science", "opus", "Deity", False, "Greece", "Last from the start: 37 techs to Greece's 68"),
    ("g6-sonnet-science", "son", "Prince", True, None, "Sonnet's first game, early harness"),
    ("g7-science-repeat", "opus", "Prince", True, None, "Game 3 repeated; a game crash on turn 102"),
    ("g8-opus-medium", "opusmed", "Prince", True, None, "Medium effort; 18 AI-turn hangs, fixed from game 10"),
    ("g9-fable-science", "f51", "Prince", True, None, "Led the best AI by 18 techs at turn 200"),
    ("g10-fixed-harness", "opus", "Prince", True, None, "Game 3 on the fixed harness"),
    ("g11-fable-fixed", "f51", "Prince", False, "Greece", "Had 4 of 5 space projects when Greece won"),
    ("g12-fable52-fixed", "f52", "Prince", True, None, "Tall, 7 cities; no AI built a Spaceport"),
    ("g13-sonnet-fixed", "son", "Prince", True, None, "Wide, 14 cities"),
    ("g14-fable52-repeat", "f52", "Prince", True, None, "Game 12 repeated; 1st in score, 21 techs ahead"),
    ("g15-fable52-deity", "f52", "Deity", False, "Greece", "Spain and Rome took 3 cities, the capital among them"),
    ("g16-fable52-emperor", "f52", "Emperor", False, "Greece", "Spain took the capital on turn 86"),
    ("g17-fable52-king", "f52", "King", True, None, "1st in score; no war against it"),
    ("g18-fable52-emperor-repeat", "f52", "Emperor", False, "Greece", "Highest science by the end, still 10 techs behind"),
    ("g19-opus-king", "opus", "King", True, None, "Close: Greece and America had 4 of 5 space projects"),
    ("g20-opus-emperor", "opus", "Emperor", False, "America", "Spain took Kish; behind in techs all game"),
    ("g21-opus-emperor-repeat", "opus", "Emperor", False, "Greece", "Game 20 repeated; Rome and Egypt took a city each"),
    ("g22-sonnet-king", "son", "King", True, None, "Close: America and Spain had 4 of 5; replayed turns 200 to 204"),
]
PLAYING = []
OTHER = [  # setups off the ladder
    ("g1-standard", "Opus 5.5 at Quick speed, with the playbook", None),
    ("g2-baseline", "Opus 5.5 at Quick speed, rules only", None),
    ("g4-domination", "Opus 5.5 with a Domination goal", None),
    ("g23-haiku-prince", "Haiku 5.5 on Prince",
     {"result": "Stopped on turn 83 for the Opus games below; 7th of 8 in score", "usd": 2.43, "wall_h": 1.4}),
    ("h2-one-opus", "Hotseat: 1 Opus 5.5 seat, 7 AI civs",
     {"result": "Science victory on turn 168", "usd": 78.02, "wall_h": 2.9}),
    ("h1-four-opus", "Hotseat: 4 Opus 5.5 seats, 4 AI civs",
     {"result": "Science victory on turn 157 by Rome, an Opus seat", "usd": 277.02, "wall_h": 12.2}),
]


def gnum(gid: str) -> str:
    return gid.split("-")[0].upper()


def game_rows():
    rows = []
    for gid, mk, level, won, winner, note in LADDER:
        g = report.load(gid, REPO / "results" / gid)
        rank = next((i + 1 for i, s in enumerate(g["standings"]) if s["agent"]), None)
        turn = g["last_turn"]
        rows.append({
            "id": gid, "n": gnum(gid), "model": mk, "level": level, "won": won, "winner": winner, "note": note,
            "turn": turn, "rank": rank, "usd": g["usd"], "per_turn": g["usd_per_turn"], "hours": g["wall_h"],
            "median_s": g["median_s"], "lead_end": g["lead"][-1][1] if g["lead"] else None,
            "lead": [[t, v] for t, v in g["lead"]],
            "result": f"Science victory on turn {turn}" if won else f"{winner} won a Science victory on turn {turn}",
        })
    return rows


def hex_svg(w: int) -> str:
    h = w * 2 / 3 ** 0.5
    pts = [(w / 2, 1), (w - 1, h / 4), (w - 1, 3 * h / 4), (w / 2, h - 1), (1, 3 * h / 4), (1, h / 4)]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts), h


HEX_W = 56
HEX_PTS, HEX_H = hex_svg(HEX_W)


def hex_tile(r: dict | None, mk: str, i: int, playing: dict | None = None) -> str:
    color = dict((m[0], m[3]) for m in MODELS)[mk]
    name = next(f"{m[1]}" + (", medium effort" if m[0] == "opusmed" else "") for m in MODELS if m[0] == mk)
    if playing:
        tip = f"<b>{gnum(playing[0])}, {name} on {playing[2]}</b><br>Playing now. {playing[3]}."
        return (f'<span class="tile playing" style="--c:var(--{color});--i:{i}" tabindex="0" data-tip="{html.escape(tip)}" '
                f'aria-label="{html.escape(gnum(playing[0]))}: playing now">'
                f'<svg viewBox="0 0 {HEX_W} {HEX_H:.1f}" aria-hidden="true"><polygon points="{HEX_PTS}"/></svg>'
                f'<span class="num">now</span><span class="gid">{gnum(playing[0])}</span></span>')
    cls = "won" if r["won"] else "lost"
    tip = (f"<b>{r['n']}, {name} on {r['level']}</b><br>{html.escape(r['result'])}<br>"
           f"{r['rank']} of 8 in score, ${r['usd']:.2f}, {r['hours']} h<br><span class=tipnote>{html.escape(r['note'])}</span>")
    label = f"{r['n']}: {'won' if r['won'] else 'lost'}, turn {r['turn']}"
    return (f'<a class="tile {cls}" style="--c:var(--{color});--on:var(--on-{color});--i:{i}" href="{GH}{r["id"]}" '
            f'data-tip="{html.escape(tip)}" aria-label="{html.escape(label)}">'
            f'<svg viewBox="0 0 {HEX_W} {HEX_H:.1f}" aria-hidden="true"><polygon points="{HEX_PTS}"/></svg>'
            f'<span class="num">{r["turn"]}</span><span class="gid">{r["n"]}</span></a>')


def ladder_html(rows) -> str:
    out = ['<div class="ladder" role="table" aria-label="Wins and losses by model and difficulty">',
           '<div class="lrow lhead" role="row"><span role="columnheader" class="lcorner"></span>']
    for lv, sub in LEVELS:
        out.append(f'<span role="columnheader" class="lvl"><b>{lv}</b><small>{sub}</small></span>')
    out.append("</div>")
    for ci, (mk, name, detail, color) in enumerate(MODELS):
        mine = [r for r in rows if r["model"] == mk]
        wins = sum(r["won"] for r in mine)
        out.append(f'<div class="lrow" role="row" style="--c:var(--{color})">'
                   f'<span class="lname" role="rowheader"><i class="sw" aria-hidden="true"></i>'
                   f'<b>{name}</b><small>{detail}, ' + (f'won {wins} of {len(mine)}' if mine else 'first game playing') + '</small></span>')
        for li, (lv, _) in enumerate(LEVELS):
            cell = [r for r in mine if r["level"] == lv]
            tiles = [hex_tile(r, mk, li) for r in sorted(cell, key=lambda r: int(r["n"][1:]))]
            tiles += [hex_tile(None, mk, li, p) for p in PLAYING if p[1] == mk and p[2] == lv]
            body = "".join(tiles) or '<span class="empty">not played</span>'
            out.append(f'<span class="lcell" role="cell"><span class="lvlm">{lv}</span><span class="tiles">{body}</span></span>')
        out.append("</div>")
    out.append("</div>")
    return "\n".join(out)


def model_table(rows) -> str:
    out = ['<table class="mt"><thead><tr><th>Model</th><th class="r">Won</th>'
           '<th class="r">Win turns</th><th class="r">Cost per win</th><th class="r">Cost per turn</th>'
           '<th class="r hide-s">Seconds per turn</th></tr></thead><tbody>']
    for mk, name, detail, color in MODELS:
        mine = [r for r in rows if r["model"] == mk]
        if not mine:  # a model still playing its first game
            continue
        wins = [r for r in mine if r["won"]]
        wt = sorted(r["turn"] for r in wins)
        wc = sorted(r["usd"] for r in wins)
        span = lambda xs, f, g=None: (f(xs[0]) if xs[0] == xs[-1] else f"{f(xs[0])}-{(g or f)(xs[-1])}") if xs else "none"  # noqa: E731
        pt = statistics.median(r["per_turn"] for r in mine)
        sec = statistics.median(r["median_s"] for r in mine)
        out.append(f'<tr style="--c:var(--{color})"><td><i class="sw" aria-hidden="true"></i>{name} '
                   f'<span class="muted{"" if mk == "opusmed" else " hide-s"}">{detail}</span></td>'
                   f'<td class="r nowrap">{len(wins)} of {len(mine)}</td>'
                   f'<td class="r nowrap">{span(wt, str)}</td><td class="r nowrap">{span(wc, lambda v: f"${v:.0f}", lambda v: f"{v:.0f}")}</td>'
                   f'<td class="r">${pt:.2f}</td><td class="r hide-s">{sec:.0f}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


def ledger(rows) -> str:
    mx = max(r["usd"] for r in rows)
    names = {m[0]: m[1] + (" medium" if m[0] == "opusmed" else "") for m in MODELS}
    colors = {m[0]: m[3] for m in MODELS}
    out = ['<table class="ledger"><thead><tr><th>Game</th><th>Model</th><th>Level</th><th>Result</th>'
           '<th class="r hide-s">Rank</th><th class="r hide-s">Tech gap</th><th class="costh">Cost</th>'
           '<th class="r hide-s">Hours</th><th class="hide-m">Note</th></tr></thead><tbody>']
    for r in sorted(rows, key=lambda r: int(r["n"][1:])):
        res = (f'<span class="long">{"Won" if r["won"] else "Lost"}, turn {r["turn"]}</span>'
               f'<span class="short">turn {r["turn"]}</span>')
        lead = f"{r['lead_end']:+d}" if r["lead_end"] else "level"
        who = "" if r["won"] else f'<span class="muted long">, {r["winner"]} won</span>'
        out.append(f'<tr style="--c:var(--{colors[r["model"]]})"><td><a href="{GH}{r["id"]}">{r["n"]}</a></td>'
                   f'<td class="nowrap"><i class="sw" aria-hidden="true"></i>{names[r["model"]]}</td><td>{r["level"]}</td>'
                   f'<td class="nowrap"><i class="res {"won" if r["won"] else "lost"}" aria-hidden="true"></i>{res}'
                   f'{who}</td>'
                   f'<td class="r hide-s nowrap">{r["rank"]} of 8</td><td class="r hide-s">{lead}</td>'
                   f'<td class="cost"><span class="track"><span class="bar" style="width:{r["usd"] / mx * 100:.1f}%"></span></span>'
                   f'<span class="v">${r["usd"]:.2f}</span></td><td class="r hide-s">{r["hours"]}</td>'
                   f'<td class="hide-m muted">{html.escape(r["note"])}</td></tr>')
    for gid, mk, lv, note in PLAYING:
        out.append(f'<tr style="--c:var(--{colors[mk]})"><td>{gnum(gid)}</td><td class="nowrap"><i class="sw" aria-hidden="true"></i>'
                   f'{names[mk]}</td><td>{lv}</td><td class="nowrap"><i class="res playing" aria-hidden="true"></i><span class="long">Playing now</span><span class="short">now</span></td>'
                   f'<td class="r hide-s"></td><td class="r hide-s"></td><td class="cost"></td><td class="r hide-s"></td>'
                   f'<td class="hide-m muted">{html.escape(note)}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


# Opus 5.5 with other civs and goals, on Prince. (id, civ, goal, status when not finished)
VARIANTS = [
    ("g4-domination", "Sumeria (Gilgamesh)", "Domination", None),
    ("g24-opus-scythia-domination", "Scythia (Tomyris)", "Domination", None),
    ("g25-opus-arabia-religious", "Arabia (Saladin)", "Religious", None),
    ("g26-opus-france-culture", "France (Catherine de Medici)", "Culture", None),
    ("g27-opus-france-culture-fixed", "France (Catherine de Medici), fixed harness", "Culture", None),
    ("g28-opus-aztec-domination", "Aztec (Montezuma)", "Domination", None),
    ("g29-opus-russia-religious", "Russia (Peter the Great)", "Religious", None),
    ("g30-opus-germany-science", "Germany (Barbarossa)", "Science", None),
    ("g31-opus-russia-religious-fixed", "Russia (Peter the Great), fixed harness", "Religious", None),
    ("g32-opus-greece-culture", "Greece (Pericles)", "Culture", None),
    ("g33-opus-india-religious", "India (Gandhi)", "Religious", None),
    ("g34-opus-japan-domination", "Japan (Hojo Tokimune)", "Domination", None),
    ("g35-opus-china-science", "China (Qin Shi Huang)", "Science", None),
    ("g36-opus-kongo-culture", "Kongo (Mvemba a Nzinga)", "Culture", None),
    ("g37-opus-rome-domination", "Rome (Trajan)", "Domination", None),
    ("g38-opus-spain-religious", "Spain (Philip II)", "Religious", None),
    ("g39-opus-egypt-culture", "Egypt (Cleopatra)", "Culture", None),
    ("g40-opus-norway-domination-emperor", "Norway (Harald Hardrada), Emperor", "Domination", None),
    ("g41-opus-england-domination-king", "England (Victoria), King", "Domination", None),
    ("g42-opus-america-culture-emperor", "America (Teddy Roosevelt), Emperor", "Culture", None),
    ("g43-opus-aztec-domination-rerun", "Aztec (Montezuma), game 28 rerun, no leak", "Domination", None),
    ("g44-opus-brazil-religious-king", "Brazil (Pedro II), King", "Religious", None),
    ("g45-opus-aztec-domination-king", "Aztec (Montezuma), King, game 43's seed", "Domination", "Stopped on turn 56"),
]


def variants_table() -> str:
    out = ['<table class="ledger other"><thead><tr><th>Game</th><th>Civ</th><th>Goal</th><th>Result</th>'
           '<th class="r">Cost</th><th class="r hide-s">Hours</th></tr></thead><tbody>']
    for gid, civ, goal, status in VARIANTS:
        if status:
            res, usd, hrs = status, "", ""
        else:
            g = report.load(gid, REPO / "results" / gid)
            res, usd, hrs = g["result"], f"${g['usd']:.2f}", g["wall_h"]
        num = gnum(gid) if status else f'<a href="{GH}{gid}">{gnum(gid)}</a>'
        out.append(f'<tr><td>{num}</td><td>{html.escape(civ)}</td><td>{goal}</td>'
                   f'<td>{html.escape(res)}</td><td class="r">{usd}</td><td class="r hide-s">{hrs}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


def other_table() -> str:
    out = ['<table class="ledger other"><thead><tr><th>Game</th><th>Setup</th><th>Result</th><th class="r">Cost</th>'
           '<th class="r hide-s">Hours</th></tr></thead><tbody>']
    for gid, setup, fixed in OTHER:
        if fixed:
            res, usd, hrs = fixed["result"], fixed["usd"], fixed["wall_h"]
        else:
            g = report.load(gid, REPO / "results" / gid)
            res, usd, hrs = g["result"], g["usd"], g["wall_h"]
        out.append(f'<tr><td><a href="{GH}{gid}">{gnum(gid)}</a></td><td>{html.escape(setup)}</td>'
                   f'<td>{html.escape(res)}</td><td class="r">${usd:.2f}</td><td class="r hide-s">{hrs}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="~/tailscale-share/civ6-benchmarks/index.html")
    a = ap.parse_args()
    rows = game_rows()
    data = {"games": [{k: r[k] for k in ("n", "id", "model", "level", "won", "winner", "turn", "rank", "usd",
                                        "per_turn", "hours", "lead", "result")} for r in rows],
            "models": [{"key": m[0], "name": m[1] + (" medium" if m[0] == "opusmed" else ""), "color": m[3]} for m in MODELS
                       if any(r["model"] == m[0] for r in rows)],
            "levels": [lv for lv, _ in LEVELS]}
    page = (Path(__file__).parent / "page.html").read_text()
    _w = {16: 'Sixteen', 17: 'Seventeen', 18: 'Eighteen', 19: 'Nineteen', 20: 'Twenty', 21: 'Twenty-one', 22: 'Twenty-two', 23: 'Twenty-three', 24: 'Twenty-four', 25: 'Twenty-five'}
    page = page.replace("__COUNT__", _w.get(len(LADDER), str(len(LADDER))))
    page = (page.replace("__LADDER__", ladder_html(rows)).replace("__MODELS__", model_table(rows))
                .replace("__LEDGER__", ledger(rows)).replace("__OTHER__", other_table()).replace("__VARIANTS__", variants_table())
                .replace("__BUILT__", datetime.now().strftime("%-d %B %Y, %H:%M"))
                .replace("__DATA__", json.dumps(data, separators=(",", ":")).replace("</", "<\\/")))
    out = Path(a.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    print(f"wrote {out} ({len(page) // 1024} KB, {len(rows)} ladder games)")


if __name__ == "__main__":
    main()
