"""Tests for the war room collector. Run: python3 -m unittest tools/warroom/test_collect.py"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collect as C  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "vendor" / "civ6-mcp" / "fixtures"


def jl(rows) -> str:
    return "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)


class TailTest(unittest.TestCase):
    def read(self, tail: C.Tail, path: Path, tail_from=None):
        size = path.stat().st_size
        plan = tail.plan(size, tail_from)
        if not plan:
            return [], False
        start, length = plan
        with open(path, "rb") as f:
            f.seek(start)
            data = f.read(length)
        return tail.apply(start, data)

    def test_incremental_partial_and_rewrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.jsonl"
            p.write_bytes(b'{"n":1}\n{"n":2}\n{"n":')
            t = C.Tail()
            lines, reset = self.read(t, p)
            self.assertEqual([json.loads(x)["n"] for x in lines], [1, 2])
            self.assertFalse(reset)
            with open(p, "ab") as f:
                f.write(b'3}\n')
            lines, _ = self.read(t, p)
            self.assertEqual([json.loads(x)["n"] for x in lines], [3])
            self.assertEqual(self.read(t, p), ([], False))
            # rewrite in place (like diary.merge_agent_reflections): earlier row grows
            p.write_bytes(b'{"n":1,"reflections":"merged"}\n{"n":2}\n{"n":3}\n{"n":4}\n')
            lines, reset = self.read(t, p)
            self.assertTrue(reset)
            lines, reset = self.read(t, p)
            self.assertEqual([json.loads(x)["n"] for x in lines], [1, 2, 3, 4])

    def test_truncated_file_restarts(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.jsonl"
            p.write_bytes(b'{"n":1}\n{"n":2}\n')
            t = C.Tail()
            self.read(t, p)
            p.write_bytes(b'{"n":9}\n')
            lines, _ = self.read(t, p)
            self.assertEqual([json.loads(x)["n"] for x in lines], [9])

    def test_big_file_first_read_starts_near_end(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "log.jsonl"
            p.write_text(jl({"n": i, "pad": "x" * 50} for i in range(200)))
            t = C.Tail()
            lines, _ = self.read(t, p, tail_from=1000)
            ns = [json.loads(x)["n"] for x in lines]
            self.assertTrue(0 < len(ns) < 30)
            self.assertEqual(ns[-1], 199)


class SanitizerTest(unittest.TestCase):
    def test_redacts_private_bits(self):
        s = C.Sanitizer(["zenbook", "player"])
        out = s.text(
            "mail a.b@example.com, read /home/u/.claude-x@y.z/projects/p/s.jsonl and C:\\Users\\player\\.civ6-mcp\\log.jsonl "
            "via zenbook at 100.64.1.2 or box.tail1234.ts.net; ~/notes.txt; ask player"
        )
        for bad in ("@example.com", "/home", "Users", "zenbook", "100.64", "ts.net", "notes.txt", "player"):
            self.assertNotIn(bad, out)

    def test_keeps_game_text(self):
        s = C.Sanitizer(["zenbook"])
        text = "T161-170: build 2/3 campuses, science 80.5 vs Rome. See https://civ6.fandom.com/wiki/Campus"
        self.assertEqual(s.text(text), text)


def assistant(mid, blocks, ts, stop="tool_use", usage=None, model="claude-opus-5-5"):
    u = usage or {"input_tokens": 10, "output_tokens": 100, "cache_read_input_tokens": 1000,
                  "cache_creation_input_tokens": 200,
                  "cache_creation": {"ephemeral_5m_input_tokens": 50, "ephemeral_1h_input_tokens": 150}}
    return [{"type": "assistant", "timestamp": ts, "message": {"id": mid, "model": model, "content": [b],
             "stop_reason": stop, "usage": u}} for b in blocks]


def result(tid, ts, err=False):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tid, "content": "ok", "is_error": err}]}}


class TranscriptTest(unittest.TestCase):
    PRICES = {"claude-opus-5-5": {"input": 4, "output": 20, "cache_write_5m": 5, "cache_write_1h": 8, "cache_read": 0.2}}

    def write(self, d, name, rows):
        p = Path(d) / name
        p.write_text(jl(rows))
        return p

    def test_usage_once_per_message_and_cost(self):
        with tempfile.TemporaryDirectory() as d:
            rows = assistant("m1", [{"type": "thinking", "thinking": ""}, {"type": "text", "text": "Hi"},
                                    {"type": "tool_use", "id": "t1", "name": "mcp__civ6__get_units", "input": {}}],
                             "2026-11-06T10:00:00Z")
            p = self.write(d, "s.jsonl", rows)
            t = C.Transcript(p)
            t.update()
            u = C.usage_totals([t], self.PRICES)
            self.assertEqual(u["requests"], 1)
            self.assertEqual((u["input"], u["output"], u["cache_read"], u["cache_write_5m"], u["cache_write_1h"]), (10, 100, 1000, 50, 150))
            want = (10 * 4 + 100 * 20 + 1000 * 0.2 + 50 * 5 + 150 * 8) / 1e6
            self.assertAlmostEqual(u["usd"], want, places=4)
            self.assertIsNone(C.usage_totals([t], {})["usd"])

    def test_status_reasoning_and_tools(self):
        with tempfile.TemporaryDirectory() as d:
            rows = []
            rows += assistant("m1", [{"type": "thinking", "thinking": "Plan the campus."},
                                     {"type": "text", "text": "Building a campus."},
                                     {"type": "tool_use", "id": "t1", "name": "mcp__civ6__set_city_production",
                                      "input": {"city_id": 1, "item": "DISTRICT_CAMPUS"}}], "2026-11-06T10:00:00Z")
            rows.append(result("t1", "2026-11-06T10:00:02Z"))
            p = self.write(d, "s.jsonl", rows)
            t = C.Transcript(p)
            t.update()
            act = C.agent_activity([t], game_over=False)
            self.assertEqual(act["status"], "thinking")
            self.assertEqual(act["reasoning"]["kind"], "thinking")
            self.assertEqual(act["reasoning"]["text"], "Plan the campus.")
            self.assertEqual(act["tools"][0]["name"], "set_city_production")
            self.assertTrue(act["tools"][0]["ok"])
            self.assertIn("item=DISTRICT_CAMPUS", act["tools"][0]["args"])

            with open(p, "a") as f:  # text-only message, then a pending end_turn
                f.write(jl(assistant("m2", [{"type": "thinking", "thinking": ""}, {"type": "text", "text": "Ending the turn."},
                                            {"type": "tool_use", "id": "t2", "name": "mcp__civ6__end_turn", "input": {}}],
                                     "2026-11-06T10:01:00Z")))
            t.update()
            act = C.agent_activity([t], game_over=False)
            self.assertEqual(act["status"], "waiting")
            self.assertEqual(act["reasoning"], {"kind": "text", "text": "Ending the turn.", "ts": C.parse_ts("2026-11-06T10:01:00Z")})
            self.assertEqual(act["earlier"][0]["text"], "Plan the campus.")
            with open(p, "a") as f:
                f.write(jl([result("t2", "2026-11-06T10:02:00Z")]))
                f.write(jl(assistant("m3", [{"type": "tool_use", "id": "t3", "name": "mcp__civ6__unit_action", "input": {"unit_id": 5}}],
                                     "2026-11-06T10:02:05Z")))
            t.update()
            self.assertEqual(C.agent_activity([t], False)["status"], "acting")
            with open(p, "a") as f:
                f.write(jl([result("t3", "2026-11-06T10:02:06Z", err=True)]))
                f.write(jl(assistant("m4", [{"type": "text", "text": "Stopping."}], "2026-11-06T10:03:00Z", stop="end_turn")))
            t.update()
            act = C.agent_activity([t], False)
            self.assertEqual(act["status"], "done")
            self.assertFalse(act["tools"][0]["ok"])
            self.assertEqual(C.agent_activity([t], True)["status"], "done")

    def test_sessions_and_subagents_sum(self):
        with tempfile.TemporaryDirectory() as d:
            a = self.write(d, "a.jsonl", assistant("m1", [{"type": "text", "text": "one"}], "2026-11-06T10:00:00Z"))
            b = self.write(d, "b.jsonl", assistant("m1", [{"type": "text", "text": "one"}], "2026-11-06T10:00:00Z")
                           + assistant("m2", [{"type": "text", "text": "two"}], "2026-11-06T11:00:00Z"))
            sub = Path(d) / "b" / "subagents"
            sub.mkdir(parents=True)
            (sub / "agent-x.jsonl").write_text(jl(assistant("m3", [{"type": "text", "text": "sub"}], "2026-11-06T11:00:01Z")))
            feed = C.AgentFeed()
            txs = feed.sync([str(a), str(b)])
            u = C.usage_totals(txs, self.PRICES)
            self.assertEqual(u["requests"], 3)  # m1 copied into the resumed session counts once
            act = C.agent_activity(txs, False)
            self.assertEqual(act["sessions"], 2)
            self.assertEqual(act["reasoning"]["text"], "two")


class TelemetryTest(unittest.TestCase):
    def test_fixture_game_with_game_over(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("diary_demo_elo4.jsonl", "log_demo_elo4.jsonl"):
                (Path(d) / name).write_bytes((FIXTURES / name).read_bytes())
            tele = C.Telemetry(C.LocalSource(Path(d)))
            tele.poll(["demo_elo4"])
            manifest = {"title": "t", "agents": [{"name": "Opus", "pid": None, "transcripts": []}]}
            st = C.build_state(manifest, tele, [C.AgentFeed()], {})
            self.assertEqual(st["game"]["turn"], 195)
            self.assertEqual(st["game"]["game_over"]["winner_civ"], "India")
            self.assertEqual(st["game"]["game_over"]["victory_type"], "Religious")
            self.assertEqual(len(st["civs"]), 4)
            ag = st["agents"][0]
            self.assertEqual((ag["pid"], ag["civ"], ag["status"]), (0, "Rome", "done"))
            self.assertEqual(ag["reflections"]["turn"], 195)
            self.assertIsNone(st["map"])

    def test_auto_key_and_run_id_files(self):
        with tempfile.TemporaryDirectory() as d:
            dd = Path(d)
            (dd / "diary_old_5_crimson-amber-falcon-47.jsonl").write_text(jl([{"turn": 1, "pid": 0, "civ": "X"}]))
            time.sleep(0.01)
            rows = [{"turn": 3, "pid": 0, "civ": "CIVILIZATION_KONGO", "is_agent": True, "score": 9}]
            (dd / "diary_kongo_-12_ashen-cobalt-citadel-07.jsonl").write_text(jl(rows))
            (dd / "diary_kongo_-12_ashen-cobalt-citadel-07_cities.jsonl").write_text("{}\n")
            tele = C.Telemetry(C.LocalSource(dd))
            tele.poll([])
            self.assertEqual(tele.keys, ["kongo_-12"])
            self.assertEqual(list(tele.diary_rows()), [(3, 0)])
            self.assertIsNone(tele.status["note"])
            tele = C.Telemetry(C.LocalSource(dd))
            tele.poll(["kongo_20261106"])  # a key that matches nothing falls back to the newest game
            self.assertEqual(tele.keys, ["kongo_-12"])
            self.assertIn("matched no files", tele.status["note"])
            tele = C.Telemetry(C.LocalSource(dd))
            tele.poll(["old_5"])  # a key that matches is kept even if it is not the newest
            self.assertEqual(tele.keys, ["old_5"])

    def test_map_static_plus_deltas(self):
        with tempfile.TemporaryDirectory() as d:
            dd = Path(d)
            static = {"gridW": 3, "gridH": 2, "terrain": [0, -1, 0, 0, 0, -1] * 3 + [16, 1, 0, 0, 0, -1] * 3,
                      "initialOwners": [0, -1, -1, -1, -1, -1], "initialCities": [{"x": 0, "y": 0, "pid": 0, "pop": 1, "name": "A"}],
                      "players": [{"pid": 0, "civ": "CIVILIZATION_ROME"}, {"pid": 9, "civ": "CIVILIZATION_GENEVA", "csType": "Scientific"}],
                      "initialTurn": 1}
            (dd / "mapstatic_rome_1_r.json").write_text(json.dumps(static))
            (dd / "mapturns_rome_1_r.jsonl").write_text(jl([
                {"turn": 1}, {"turn": 2, "owners": [1, 0, 5, 9], "cities": [{"x": 0, "y": 0, "pid": 0, "pop": 3, "name": "A"}]}]))
            tele = C.Telemetry(C.LocalSource(dd))
            tele.poll(["rome_1"])
            m = tele.map_state()
            self.assertEqual(list(base64.b64decode(m["owners"])), [1, 1, 0, 0, 0, 10])
            self.assertEqual(list(base64.b64decode(m["terrain"])), [0, 0, 0, 16, 16, 16])
            self.assertEqual(list(base64.b64decode(m["features"])), [0, 0, 0, 2, 2, 2])
            self.assertEqual(m["cities"][0]["pop"], 3)

    def test_parse_remote_output(self):
        ft = int((1_800_000_000 + 11644473600) * 1e7)
        out = "\r\n".join(["WR|DIR", f"F|diary_a_1.jsonl|12|{ft}", "C|diary_a_1.jsonl|0|" + base64.b64encode(b'{"a":1}\n').decode(),
                           "X|log_a_1.jsonl", "ERRORS:", "  oops", "WR|END", ""])
        f = C.parse_remote(out)
        self.assertTrue(f.ok)
        self.assertAlmostEqual(f.files["diary_a_1.jsonl"][1], 1_800_000_000, places=3)
        self.assertEqual(f.chunks["diary_a_1.jsonl"], (0, b'{"a":1}\n'))
        self.assertFalse(C.parse_remote("WR|NODIR\r\n").has_dir)
        self.assertFalse(C.parse_remote("").ok)

    def test_remote_script_only_reads(self):
        script = C.RemoteSource(None).script({"diary_a.jsonl": (0, 10), "../evil.txt": (0, 10)})
        self.assertNotIn("evil", script)
        for verb in ("Set-Content", "Remove-Item", "Out-File", "New-Item", "Start-Process", "Register-Scheduled", "FileAccess]::Write", "FileMode]::Create"):
            self.assertNotIn(verb, script)


class EndToEndTest(unittest.TestCase):
    def test_demo_state_is_private(self):
        with tempfile.TemporaryDirectory() as d:
            demo, out = Path(d) / "demo", Path(d) / "out"
            subprocess.run([sys.executable, str(REPO / "tools/warroom/make_demo.py"), "--out", str(demo)], check=True, capture_output=True)
            self.assertEqual(C.main(["--manifest", str(demo / "manifest-4.json"), "--out", str(out),
                                     "--local-dir", str(demo / "civ6-mcp"), "--once", "--publish"]), 0)
            raw = (out / "state.json").read_text()
            st = json.loads(raw)
            self.assertEqual(len(st["agents"]), 4)
            self.assertEqual(st["game"]["turn"], 161)
            self.assertEqual(len(st["civs"]), 8)
            self.assertTrue(st["map"] and st["map"]["cities"])
            self.assertEqual({a["status"] for a in st["agents"]}, {"thinking", "acting", "waiting"})
            for bad in (d, "transcripts", ".jsonl", "/home", "@"):
                self.assertNotIn(bad, raw)
            for f in ("index.html", "app.js", "style.css", "fonts/BarlowCondensed-600.woff2"):
                self.assertTrue((out / f).exists(), f)


if __name__ == "__main__":
    unittest.main()
