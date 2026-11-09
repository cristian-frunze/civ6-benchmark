"""Measure the diplomacy-pause trap in single-player games: python3 tools/turn_trap.py g3-science g6-sonnet-science

The trap: end_turn pauses for an AI proposal, the agent answers, the game moves on to the agent's
next turn, and the agent's next end_turn ends that new turn before it gives any order."""
import glob
import json
import sys
from pathlib import Path


for g in sys.argv[1:]:
    f = glob.glob(str(Path("~/.civ6-bench/runs").expanduser() / g / "archive" / "civ6mcp" / "log_*.jsonl"))[0]
    rows = [json.loads(l) for l in open(f) if l.strip()]
    rows = [r for r in rows if r.get("type") == "tool_call"]
    pauses = advanced = trapped = partial = 0
    i = 0
    while i < len(rows):
        r = rows[i]
        if r.get("tool") == "end_turn" and "Turn paused" in (r.get("result") or ""):
            pauses += 1
            tp = r.get("turn") or 0
            # find the next end_turn after this pause
            j = i + 1
            while j < len(rows) and rows[j].get("tool") != "end_turn":
                j += 1
            if j < len(rows) and (rows[j].get("turn") or 0) > tp:
                advanced += 1
                # from here to the end_turn that advances, did the agent move any unit?
                k, unit_orders = j, 0
                while k < len(rows):
                    x = rows[k]
                    res = x.get("result") or ""
                    if x.get("tool") in ("unit_action", "issue_orders", "city_attack") and not res.startswith("Error") \
                            and "NO_MOVES" not in res:
                        unit_orders += 1
                    # An end_turn that reports the paused turn's own change ("Turn <tp> -> ...") ends nothing: civ6-mcp
                    # reports a turn end still in flight that way (always from game 8 on, and before that when the new
                    # turn had no blockers). The new turn ends at the next end_turn after it.
                    if x.get("tool") == "end_turn" and res.startswith("Turn ") and not res.startswith(f"Turn {tp} ->"):
                        break
                    if x.get("tool") == "end_turn" and "Turn paused" in res:
                        break
                    k += 1
                if unit_orders == 0:
                    trapped += 1
            i = j
            continue
        i += 1
    print(f"{g}: {pauses} pauses; {advanced} times the game had moved to the next turn before the agent's next "
          f"end_turn; {trapped} of those turns ended with no unit order")
