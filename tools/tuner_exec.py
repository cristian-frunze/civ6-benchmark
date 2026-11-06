"""Run Lua in a named Civ 6 Lua state over FireTuner and print every output line.
Usage: tuner_exec.py <state name> <lua file> [timeout seconds]"""
import asyncio, re, sys
sys.path.insert(0, "src")
from civ_mcp.tuner_client import connect, handshake, send_message, recv_message_timeout, TAG_COMMAND

END = "---BENCH-END---"

async def main():
    want, path = sys.argv[1], sys.argv[2]
    timeout = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    code = open(path, encoding="utf-8").read() + f'\nprint("{END}")\n'
    r, w = await connect("127.0.0.1", 4318)
    _, states = await handshake(r, w)
    names = [str(s) for s in states]
    idx = next((i for i, n in enumerate(names) if n == want and not n.isdigit()), None)
    if idx is None:
        idx = next((i for i, n in enumerate(names) if want.lower() in n.lower() and not n.isdigit()), None)
    if idx is None:
        print("STATES:", names); return
    sid = int(names[idx - 1]) if idx > 0 and names[idx - 1].isdigit() else idx
    await send_message(w, TAG_COMMAND, f"CMD:{sid}:{code}")
    while True:
        msg = await recv_message_timeout(r, timeout=timeout)
        if msg is None:
            print("[timeout]"); break
        text = msg.payload or ""
        for line in text.splitlines():
            line = re.sub(r"^O\x00?[^:]*: ", "", line)  # strip the tuner's "O<NUL><state>: " prefix
            if line.strip() == END:
                w.close(); return
            if line.strip():
                print(line)
    w.close()

asyncio.run(main())
