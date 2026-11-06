"""Call civ6-mcp tools directly over streamable HTTP, for smoke tests and timing (no model involved).

    uv run --with mcp==1.26.0 python tools/mcp_call.py [--url URL] tool [json-args] [tool [json-args] ...]
    uv run --with mcp==1.26.0 python tools/mcp_call.py --list
"""

import argparse
import asyncio
import json
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:18771/mcp")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--chars", type=int, default=1500, help="print at most this many chars of each result")
    ap.add_argument("calls", nargs="*")
    a = ap.parse_args()
    async with streamablehttp_client(a.url) as (r, w, _):
        async with ClientSession(r, w) as s:
            t = time.perf_counter()
            await s.initialize()
            print(f"initialize {1000 * (time.perf_counter() - t):.0f} ms")
            if a.list:
                tools = (await s.list_tools()).tools
                print(f"{len(tools)} tools: " + ", ".join(sorted(x.name for x in tools)))
            i = 0
            while i < len(a.calls):
                name = a.calls[i]
                args = {}
                if i + 1 < len(a.calls) and a.calls[i + 1].startswith("{"):
                    args = json.loads(a.calls[i + 1])
                    i += 1
                i += 1
                t = time.perf_counter()
                res = await s.call_tool(name, args)
                ms = 1000 * (time.perf_counter() - t)
                text = "\n".join(c.text for c in res.content if getattr(c, "text", None))
                print(f"=== {name} {json.dumps(args)}  {ms:.0f} ms  {len(text)} chars{'  ERROR' if res.isError else ''}")
                print(text[: a.chars])


asyncio.run(main())
