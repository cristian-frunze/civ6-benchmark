#!/usr/bin/env python3
"""Build demo input for the war room collector.

Merges the four civ6-mcp fixture games (vendor/civ6-mcp/fixtures) into one
8-civ game (Russia, Greece, America and Rome keep their agent reflections),
adds a synthetic Pangaea map in the map-capture format, a tool log, a
heartbeat and synthetic Claude Code transcripts, and writes manifests for
1, 4 and 8 agents. The game is split across two MCP run ids, like a game that
resumed in a new MCP process.

    python3 tools/warroom/make_demo.py --out /tmp/warroom-demo [--real-transcript FILE.jsonl]

--real-transcript copies a real Claude Code transcript in as agent 1.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "vendor" / "civ6-mcp" / "fixtures"
KEY = "russia_-1066"
RUN_A, RUN_B = "ancient-amber-forge-12", "ashen-cobalt-citadel-07"
SPLIT_TURN = 80
LAST_TURN = 160
W, H = 84, 54

# (fixture, civ in fixture) -> new pid
CIVS = [
    ("elo1", "RUSSIA", 0), ("elo2", "GREECE", 1), ("elo3", "AMERICA", 2), ("elo4", "ROME", 3),
    ("elo1", "JAPAN", 4), ("elo2", "GERMANY", 5), ("elo2", "BRAZIL", 6), ("elo3", "INDIA", 7),
]
CITY_NAMES = {
    0: ["Moscow", "St. Petersburg", "Novgorod", "Kazan", "Smolensk", "Yaroslavl", "Vladivostok", "Tver"],
    1: ["Athens", "Sparta", "Corinth", "Argos", "Knossos", "Mycenae", "Delphi", "Thebes"],
    2: ["Washington", "New York", "Boston", "Philadelphia", "Chicago", "Atlanta", "Seattle", "Denver"],
    3: ["Rome", "Antium", "Cumae", "Neapolis", "Ravenna", "Arretium", "Mediolanum", "Capua"],
    4: ["Kyoto", "Osaka", "Edo", "Nara", "Kamakura", "Nagoya", "Sendai", "Hakodate"],
    5: ["Aachen", "Cologne", "Frankfurt", "Magdeburg", "Mainz", "Heidelberg", "Trier", "Nuremberg"],
    6: ["Rio de Janeiro", "Sao Paulo", "Salvador", "Brasilia", "Recife", "Manaus", "Belem", "Fortaleza"],
    7: ["Delhi", "Mumbai", "Varanasi", "Agra", "Calcutta", "Lahore", "Bangalore", "Hyderabad"],
}
CITY_STATES = [
    (8, "GENEVA", "Scientific"), (9, "KUMASI", "Cultural"), (10, "CARTHAGE", "Militaristic"),
    (11, "JERUSALEM", "Religious"), (12, "ZANZIBAR", "Trade"), (13, "BRUSSELS", "Industrial"),
]
# Civ 6 base-game terrain and feature indexes (MapEnums.lua)
GRASS, PLAINS, DESERT, TUNDRA, SNOW, COAST, OCEAN = 0, 3, 6, 9, 12, 15, 16
F_FLOOD, F_ICE, F_JUNGLE, F_FOREST, F_OASIS, F_MARSH = 0, 1, 2, 3, 4, 5


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat().replace("+00:00", "Z")


def dumps(o) -> str:
    return json.dumps(o, separators=(",", ":"))


# ── diary ───────────────────────────────────────────────────────────────


def build_diary() -> dict[int, list[dict]]:
    by_turn: dict[int, list[dict]] = {}
    for fx, civ, pid in CIVS:
        for line in open(FIXTURES / f"diary_demo_{fx}.jsonl"):
            r = json.loads(line)
            if r["civ"] != civ or r["turn"] > LAST_TURN:
                continue
            r.update(pid=pid, game=KEY, civ=f"CIVILIZATION_{civ}", is_agent=pid < 4)
            if pid >= 4:
                r.pop("reflections", None)
            by_turn.setdefault(r["turn"], []).append(r)
    for rows in by_turn.values():
        rows.sort(key=lambda r: r["pid"])
    return by_turn


# ── map ─────────────────────────────────────────────────────────────────


def wrap_dx(a: float, b: float) -> float:
    d = abs(a - b) % W
    return min(d, W - d)


def to_cube(x: int, y: int) -> tuple[int, int]:
    return x - (y - (y & 1)) // 2, y


def hex_dist(a: tuple[int, int], b: tuple[int, int]) -> int:
    best = 10**9
    for shift in (-W, 0, W):
        q1, r1 = to_cube(a[0], a[1])
        q2, r2 = to_cube(b[0] + shift, b[1])
        dq, dr = q1 - q2, r1 - r2
        best = min(best, (abs(dq) + abs(dr) + abs(dq + dr)) // 2)
    return best


def neighbors(x: int, y: int):
    deltas = [(1, 0), (1, 1), (0, 1), (-1, 0), (0, -1), (1, -1)] if y & 1 else \
             [(1, 0), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1)]
    for dx, dy in deltas:
        ny = y + dy
        if 0 <= ny < H:
            yield (x + dx) % W, ny


class Noise:
    def __init__(self, rng: random.Random, cell: int):
        self.cell = cell
        self.gw, self.gh = max(1, W // cell), H // cell + 2  # x period W/cell, so it wraps
        self.g = [[rng.random() for _ in range(self.gw)] for _ in range(self.gh)]

    def at(self, x: float, y: float) -> float:
        fx, fy = x / self.cell, y / self.cell
        x0, y0 = int(fx), int(fy)
        tx, ty = fx - x0, fy - y0
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        g = self.g
        r0, r1 = g[y0 % self.gh], g[(y0 + 1) % self.gh]
        a = r0[x0 % self.gw] * (1 - tx) + r0[(x0 + 1) % self.gw] * tx
        b = r1[x0 % self.gw] * (1 - tx) + r1[(x0 + 1) % self.gw] * tx
        return a * (1 - ty) + b * ty


def fbm(layers, x, y):
    tot = wsum = 0.0
    for wgt, n in layers:
        tot += wgt * n.at(x, y)
        wsum += wgt
    return tot / wsum


def build_terrain(rng: random.Random):
    # W is a multiple of every cell size, so the noise wraps east-west cleanly
    elev = [(1.0, Noise(rng, 12)), (0.5, Noise(rng, 6)), (0.25, Noise(rng, 3))]
    moist = [(1.0, Noise(rng, 14)), (0.5, Noise(rng, 7))]
    rough = [(1.0, Noise(rng, 7)), (0.6, Noise(rng, 3))]
    cx, cy = 6.0, H / 2  # continent straddles the east-west wrap seam
    land = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            dx, dy = wrap_dx(x, cx) / (W * 0.40), (y - cy) / (H * 0.42)
            fall = 1 - (dx * dx + dy * dy)
            land[y][x] = 0.62 * fall + 0.55 * fbm(elev, x, y) > 0.52
    tiles = []
    for y in range(H):
        lat = abs(y - (H - 1) / 2) / ((H - 1) / 2)
        for x in range(W):
            feat, hills, river = -1, 0, 0
            if not land[y][x]:
                t = COAST if any(land[ny][nx] for nx, ny in neighbors(x, y)) else OCEAN
                if lat > 0.9 or (lat > 0.84 and rng.random() < 0.4):
                    feat = F_ICE
            else:
                m = fbm(moist, x, y)
                if lat > 0.86:
                    t = SNOW
                elif lat > 0.70:
                    t = TUNDRA
                elif lat < 0.38 and m < 0.42:
                    t = DESERT
                elif m < 0.52:
                    t = PLAINS
                else:
                    t = GRASS
                r = fbm(rough, x, y)
                if r > 0.74:
                    t += 2  # mountain
                elif r > 0.60:
                    t += 1  # hills
                    hills = 1
                if t % 3 != 2:
                    if t in (GRASS, PLAINS, GRASS + 1, PLAINS + 1) and m > 0.6:
                        feat = F_JUNGLE if lat < 0.3 else F_FOREST
                    elif t in (GRASS, PLAINS) and m > 0.5 and rng.random() < 0.35:
                        feat = F_FOREST
                    elif t == GRASS and m > 0.55 and rng.random() < 0.08:
                        feat = F_MARSH
                    elif t == DESERT and rng.random() < 0.03:
                        feat = F_OASIS
                    river = 1 if abs(fbm(rough, x * 1.7, y * 1.7) - 0.5) < 0.025 else 0
                    if river and t in (DESERT, PLAINS, GRASS) and feat < 0:
                        feat = F_FLOOD
            tiles.append([t, feat, hills, river, 0, -1])
    for y in range(H):
        for x in range(W):
            t = tiles[y * W + x]
            if t[0] < COAST:
                t[4] = 1 if any(tiles[ny * W + nx][0] >= COAST for nx, ny in neighbors(x, y)) else 0
    # three natural wonders (base-game feature indexes 6 and up)
    flat = [i for i, t in enumerate(tiles) if t[0] < COAST and t[0] % 3 != 2
            and sum(tiles[ny * W + nx][0] < COAST for nx, ny in neighbors(i % W, i // W)) >= 5]
    for idx, fid in zip(rng.sample(flat, 3), (10, 12, 17)):
        tiles[idx][1] = fid
    return tiles


def is_good_site(tiles, x, y) -> bool:
    t = tiles[y * W + x]
    return t[0] < COAST and t[0] % 3 != 2 and t[0] not in (SNOW, SNOW + 1) and t[1] < 6


def place_cities(rng: random.Random, tiles, diary) -> list[dict]:
    last = {r["pid"]: r for r in diary[LAST_TURN]}
    founded: dict[int, list[int]] = {}
    for turn in sorted(diary):
        for r in diary[turn]:
            prev = len(founded.get(r["pid"], []))
            founded.setdefault(r["pid"], []).extend([turn] * max(0, r["cities"] - prev))
    sites = [(x, y) for y in range(H) for x in range(W) if is_good_site(tiles, x, y)]
    cities: list[dict] = []

    def free(p, gap):
        return all(hex_dist(p, (c["x"], c["y"])) >= gap for c in cities)

    caps = []
    for pid in range(8):
        for _ in range(4000):
            p = rng.choice(sites)
            if all(hex_dist(p, q) >= 15 for q in caps) and 6 < p[1] < H - 7:
                caps.append(p)
                break
        else:
            raise SystemExit("could not place capitals")
    for pid, cap in enumerate(caps):
        turns = founded.get(pid, [1])
        own = [cap]
        cities.append({"x": cap[0], "y": cap[1], "pid": pid, "name": CITY_NAMES[pid][0], "founded": turns[0]})
        for n, ft in enumerate(turns[1:], 1):
            for _ in range(4000):
                base = rng.choice(own)
                p = rng.choice(sites)
                if 4 <= hex_dist(p, base) <= 7 and free(p, 4) and min(hex_dist(p, q) for q in caps if q != cap) >= 7:
                    own.append(p)
                    cities.append({"x": p[0], "y": p[1], "pid": pid, "name": CITY_NAMES[pid][n], "founded": ft})
                    break
    for pid, name, _ in CITY_STATES:
        for _ in range(4000):
            p = rng.choice(sites)
            if free(p, 6):
                cities.append({"x": p[0], "y": p[1], "pid": pid, "name": name.title(), "founded": 1})
                break
    for pid in range(8):
        mine = [c for c in cities if c["pid"] == pid]
        total = last[pid]["pop"]
        weights = [3.0] + [1.0 + rng.random() for _ in mine[1:]]
        for c, wgt in zip(mine, weights):
            c["final_pop"] = max(1, round(total * wgt / sum(weights)))
    for c in cities:
        c.setdefault("final_pop", rng.randint(3, 8))
    return cities


def ownership(tiles, cities, turn) -> list[int]:
    live = [c for c in cities if c["founded"] <= turn]
    owners = [-1] * (W * H)
    best = [99] * (W * H)
    for c in sorted(live, key=lambda c: c["founded"]):
        age = turn - c["founded"]
        r = 1 if age < 8 else 2 if age < 45 or c["pid"] >= 8 else 3
        for y in range(max(0, c["y"] - r), min(H, c["y"] + r + 1)):
            for dx in range(-r - 1, r + 2):
                x = (c["x"] + dx) % W
                d = hex_dist((c["x"], c["y"]), (x, y))
                i = y * W + x
                if d > r or (tiles[i][0] == OCEAN) or d >= best[i]:
                    continue
                best[i], owners[i] = d, c["pid"]
    return owners


def city_snapshot(cities, turn) -> list[dict]:
    out = []
    for c in cities:
        if c["founded"] <= turn:
            frac = min(1.0, (turn - c["founded"] + 1) / max(1, LAST_TURN - c["founded"] + 1))
            out.append({"x": c["x"], "y": c["y"], "pid": c["pid"], "pop": max(1, round(c["final_pop"] * frac)), "name": c["name"]})
    return out


def write_map(cv: Path, tiles, cities, diary_turns) -> None:
    players = [{"pid": pid, "civ": f"CIVILIZATION_{civ}"} for _, civ, pid in CIVS]
    players += [{"pid": pid, "civ": f"CIVILIZATION_{name}", "csType": t} for pid, name, t in CITY_STATES]
    flat = [v for t in tiles for v in t]
    for run, t0, turns in ((RUN_A, 1, [t for t in diary_turns if t <= SPLIT_TURN]),
                           (RUN_B, SPLIT_TURN + 1, [t for t in diary_turns if t > SPLIT_TURN] + [LAST_TURN + 1])):
        prev = ownership(tiles, cities, t0 if t0 == 1 else t0 - 1)
        static = {
            "gridW": W, "gridH": H, "terrain": flat, "initialOwners": prev,
            "initialRoutes": [-1] * (W * H), "initialCities": city_snapshot(cities, t0),
            "players": players, "initialTurn": t0,
        }
        (cv / f"mapstatic_{KEY}_{run}.json").write_text(dumps(static))
        with open(cv / f"mapturns_{KEY}_{run}.jsonl", "w") as f:
            for turn in turns:
                cur = ownership(tiles, cities, turn)
                changes = [v for i, (a, b) in enumerate(zip(prev, cur)) if a != b for v in (i, b)]
                row = {"turn": turn, "cities": city_snapshot(cities, turn)}
                if changes:
                    row["owners"] = changes
                f.write(dumps(row) + "\n")
                prev = cur


# ── tool log and heartbeat ──────────────────────────────────────────────


def write_log(cv: Path, now: float) -> None:
    tools = ["get_game_overview", "get_units", "unit_action", "get_cities", "set_city_production",
             "get_notifications", "get_tech_civics", "set_research", "end_turn"]
    for run, turns, t_end in ((RUN_A, range(1, SPLIT_TURN + 1, 7), now - 4000), (RUN_B, range(SPLIT_TURN + 1, LAST_TURN + 2, 5), now - 20)):
        with open(cv / f"log_{KEY}_{run}.jsonl", "w") as f:
            turns = list(turns)
            for n, turn in enumerate(turns):
                for k, tool in enumerate(tools):
                    ts = t_end - (len(turns) - n) * 60 + k * 6
                    result = f"{tool} result for turn {turn}. " + "Narrated detail. " * 120
                    f.write(dumps({
                        "game": KEY, "civ": "russia", "seed": -1066, "session": run[:8], "ts": ts, "turn": turn,
                        "type": "tool_call", "tool": tool, "category": "query", "params": {},
                        "result_summary": result[:200], "result": result, "duration_ms": 300 + k * 40,
                        "success": True, "agent_model": "claude-opus-5-5",
                    }) + "\n")
    (cv / "heartbeat.json").write_text(dumps({"phase": "playing", "turn": LAST_TURN + 1, "ts": now, "run_id": RUN_B, "civ": "russia", "seed": -1066}))


# ── synthetic Claude Code transcripts ───────────────────────────────────

LINES = {
    "Greece": [
        "Acropolis is done in Athens, so the theater square adjacency is +4 there. Next culture push: Amphitheater in Sparta, then a Great Writer recruit before Brazil gets Homer.",
        "Germany's military jumped to 230. My border with them is two hills and a river, so a pair of crossbowmen behind the walls of Corinth should hold. No reason to spend culture on war.",
        "Tourism is the bottleneck, not culture. I'll move the trade route from Argos to Germany's capital so the tourism bonus from the open borders applies.",
    ],
    "America": [
        "Rome is the one to watch. 305 score and a Spaceport plan. I'll keep the research alliance going and push Rocketry myself so I'm not racing from behind.",
        "Washington has the best campus adjacency on the map. Buy the University now with 410 gold instead of waiting 6 turns. That's 6 turns of +8 science.",
        "Scout reports a Roman legion stack near Boston. Probably a feint, but walls first, then the Industrial Zone.",
    ],
    "Rome": [
        "Domination target is India. Their military is 80 against my 145, and Delhi sits on flat grassland with no river. Four catapults and the legions can take it in 6 turns.",
        "Moving the second army through the pass south of Antium. Keep the Great General adjacent so every unit gets +5.",
        "Not declaring yet. I need the casus belli from the denouncement to avoid the warmonger penalty with Greece.",
    ],
    "Japan": ["Coastal cities first. Osaka's harbor gives the best production on this continent."],
    "Germany": ["Hansa in Aachen next to the commercial hub and aqueduct. That is +6 production."],
    "Brazil": ["Rainforest adjacency is the whole plan. Keep the jungle and build campuses next to it."],
    "India": ["Faith is ahead of everyone. Missionaries to Greece first, they have no religion."],
}
TOOLS_BY_CIV = {
    "Greece": [("get_game_overview", {}), ("get_cities", {}), ("set_city_production", {"city_id": 2, "item": "BUILDING_AMPHITHEATER"}),
               ("get_great_people", {}), ("recruit_great_person", {"individual_id": 41})],
    "America": [("get_game_overview", {}), ("get_tech_civics", {}), ("set_research", {"tech": "TECH_ROCKETRY"}),
                ("purchase_item", {"city_id": 0, "item": "BUILDING_UNIVERSITY", "currency": "GOLD"}), ("get_units", {})],
    "Rome": [("get_game_overview", {}), ("get_units", {}), ("unit_action", {"unit_id": 131074, "action": "move", "target_x": 41, "target_y": 22}),
             ("get_pathing_estimate", {"unit_id": 131075, "target_x": 44, "target_y": 20}), ("get_diplomacy", {})],
}


def write_transcript(path: Path, civ: str, end: str, now: float, rng: random.Random, n_turns: int = 40, thinking: bool = True) -> None:
    tools = TOOLS_BY_CIV.get(civ, [("get_game_overview", {}), ("get_cities", {}), ("get_units", {})])
    lines = LINES[civ]
    t = now - n_turns * 150 - 30
    ctx = 40_000
    out: list[dict] = []
    seq = 0

    def assistant(blocks, stop, ts):
        nonlocal seq, ctx
        seq += 1
        mid = f"msg_demo_{civ.lower()}_{seq:05d}"
        ctx += rng.randint(800, 2600)
        cw = rng.randint(600, 3000)
        usage = {"input_tokens": rng.randint(2, 9), "output_tokens": rng.randint(120, 900),
                 "cache_read_input_tokens": ctx, "cache_creation_input_tokens": cw,
                 "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": cw}}
        for b in blocks:
            out.append({"type": "assistant", "timestamp": iso(ts), "isSidechain": False,
                        "message": {"model": "claude-opus-5-5", "id": mid, "type": "message", "role": "assistant",
                                    "content": [b], "stop_reason": stop, "usage": usage}})
        if ctx > 160_000:
            ctx = 45_000  # context compaction

    def result(tid, ts, ok=True):
        out.append({"type": "user", "timestamp": iso(ts), "isSidechain": False,
                    "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tid, "content": "ok", "is_error": not ok}]}})

    out.append({"type": "user", "timestamp": iso(t), "message": {"role": "user", "content": f"You are playing {civ}. Play to win."}})
    for turn in range(n_turns):
        for k, (name, args) in enumerate(tools):
            t += rng.uniform(8, 24)
            tid = f"toolu_demo_{civ.lower()}_{turn}_{k}"
            blocks = []
            if k == 0 or rng.random() < 0.3:
                text = rng.choice(lines)
                blocks.append({"type": "thinking", "thinking": text if thinking else "", "signature": "x"})
                if not thinking:
                    blocks.append({"type": "text", "text": text})
            blocks.append({"type": "tool_use", "id": tid, "name": f"mcp__civ6__{name}", "input": args})
            assistant(blocks, "tool_use", t)
            t += rng.uniform(0.5, 3)
            result(tid, t, ok=rng.random() > 0.05)
        t += rng.uniform(4, 10)
        tid = f"toolu_demo_{civ.lower()}_{turn}_end"
        assistant([{"type": "tool_use", "id": tid, "name": "mcp__civ6__end_turn",
                    "input": {"tactical": "...", "strategic": "...", "tooling": "No issues", "planning": "...", "hypothesis": "..."}}], "tool_use", t)
        if turn == n_turns - 1 and end == "waiting":
            break
        t += rng.uniform(20, 60)
        result(tid, t)
    # shift so the transcript ends a few seconds ago, then set the final state
    last = max(datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).timestamp() for e in out)
    shift = (now - rng.uniform(3, 25)) - last
    for e in out:
        e["timestamp"] = iso(datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).timestamp() + shift)
    t = now - 2
    if end == "acting":
        name, args = tools[2]
        assistant([{"type": "thinking", "thinking": rng.choice(lines) if thinking else "", "signature": "x"},
                   {"type": "tool_use", "id": f"toolu_demo_{civ.lower()}_live", "name": f"mcp__civ6__{name}", "input": args}], "tool_use", t)
    elif end == "done":
        assistant([{"type": "text", "text": "Game over. Writing the post-mortem to the diary."}], "end_turn", t)
    path.write_text("".join(json.dumps(e) + "\n" for e in out))


# ── main ────────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--real-transcript", type=Path, help="copy this Claude Code transcript in as agent 1")
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    now = time.time()
    out = args.out
    cv, tx = out / "civ6-mcp", out / "transcripts"
    for d in (cv, tx):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    diary = build_diary()
    for run, keep in ((RUN_A, lambda t: t <= SPLIT_TURN), (RUN_B, lambda t: t > SPLIT_TURN)):
        with open(cv / f"diary_{KEY}_{run}.jsonl", "w") as f:
            for turn in sorted(diary):
                if keep(turn):
                    for r in diary[turn]:
                        f.write(dumps(r) + "\n")
    tiles = build_terrain(rng)
    cities = place_cities(rng, tiles, diary)
    write_map(cv, tiles, cities, sorted(diary))
    write_log(cv, now)

    civ_names = ["Russia", "Greece", "America", "Rome", "Japan", "Germany", "Brazil", "India"]
    ends = ["thinking", "thinking", "acting", "waiting", "thinking", "acting", "waiting", "done"]
    paths = []
    for pid, civ in enumerate(civ_names):
        p = tx / f"agent-{pid + 1}.jsonl"
        if pid == 0 and args.real_transcript:
            shutil.copyfile(args.real_transcript, p)
        else:
            write_transcript(p, civ if civ in LINES else "Japan", ends[pid], now, rng, thinking=pid % 2 == 1)
        paths.append(str(p.resolve()))
    goals = ["Science", "Culture", None, "Domination", "Science", None, "Culture", "Religious"]
    for n in (1, 4, 8):
        manifest = {
            "title": f"Demo: {n} Opus vs {8 - n} AI" if n < 8 else "Demo: 8 Opus seats",
            "game_key": KEY,
            "demo": True,
            "agents": [
                {"name": f"Opus {i + 1}", "pid": i, "goal": goals[i], "model": "claude-opus-5-5", "transcripts": [paths[i]]}
                for i in range(n)
            ],
        }
        (out / f"manifest-{n}.json").write_text(json.dumps(manifest, indent=2))
    print(f"demo written to {out}: {len(diary)} diary turns, {sum(1 for c in cities)} cities, map {W}x{H}")


if __name__ == "__main__":
    main()
