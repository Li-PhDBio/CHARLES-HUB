#!/usr/bin/env python3
"""Claude Code adapter: connects to Charles Hub via WebSocket, bridges to CC stdin/stdout."""
import asyncio
import json
import sys
import aiohttp


HUB_URL = "ws://210.34.84.181:9800/ws"


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(HUB_URL) as ws:
            print("[CC Adapter] Connected to Charles Hub", file=sys.stderr)

            async def from_hub():
                """Read messages from Hub, write to stdout (CC reads this)."""
                async for msg in ws:
                    data = json.loads(msg.data)
                    if data.get("type") == "message":
                        sys.stdout.write(json.dumps(data) + "\n")
                        sys.stdout.flush()
                    elif data.get("type") == "resume":
                        sys.stdout.write(json.dumps(data) + "\n")
                        sys.stdout.flush()

            async def to_hub():
                """Read from stdin (CC writes here), send to Hub."""
                loop = asyncio.get_event_loop()
                while True:
                    line = await loop.run_in_executor(None, sys.stdin.readline)
                    if not line:
                        break
                    try:
                        data = json.loads(line.strip())
                        await ws.send_json(data)
                    except json.JSONDecodeError:
                        print(f"[CC Adapter] Invalid JSON: {line.strip()}", file=sys.stderr)

            await asyncio.gather(from_hub(), to_hub())


if __name__ == "__main__":
    asyncio.run(main())
