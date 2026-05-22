"""WebSocket server that Claude Code connects to for message exchange."""
import asyncio
import json
from datetime import datetime, timezone
from aiohttp import web
from charles_hub.storage import Storage


class CCWebSocketServer:
    def __init__(self, host: str, port: int, storage: Storage, config):
        self.host = host
        self.port = port
        self.storage = storage
        self.config = config
        self._cc_ws: web.WebSocketResponse | None = None
        self._outgoing_queue: asyncio.Queue = asyncio.Queue()
        self._incoming_queue: asyncio.Queue = asyncio.Queue()

    @property
    def is_connected(self) -> bool:
        return self._cc_ws is not None and not self._cc_ws.closed

    async def handle_ws(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._cc_ws = ws
        self.storage.set_agent_status("zhongshu", "online")
        print(f"[WS] Claude Code connected")

        async def send_loop():
            while not ws.closed:
                try:
                    msg = await asyncio.wait_for(self._outgoing_queue.get(), timeout=1.0)
                    await ws.send_json(msg)
                except asyncio.TimeoutError:
                    pass

        async def recv_loop():
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._incoming_queue.put(data)
                elif msg.type == web.WSMsgType.ERROR:
                    break

        send_task = asyncio.create_task(send_loop())
        try:
            await recv_loop()
        finally:
            send_task.cancel()
            self._cc_ws = None
            self.storage.set_agent_status("zhongshu", "offline")
            print(f"[WS] Claude Code disconnected")
        return ws

    async def send_to_cc(self, msg: dict):
        if self.is_connected:
            await self._outgoing_queue.put(msg)
        else:
            self.storage.save_message(
                msg_id=msg.get("msg_id", f"cached_{datetime.now(timezone.utc).timestamp()}"),
                chat_id=msg.get("chat_id", ""),
                sender=msg.get("from", ""),
                content=msg.get("content", ""),
                mentioned_bots=msg.get("mentioned_bots", []),
            )

    async def send_resume(self):
        """Send offline summary on reconnect."""
        if self.is_connected:
            pending = self.storage.get_all_agent_statuses()
            await self._outgoing_queue.put({
                "type": "resume",
                "agent_statuses": pending,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    async def recv_from_cc(self) -> dict | None:
        try:
            return await asyncio.wait_for(self._incoming_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None

    def get_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/ws", self.handle_ws)
        return app

    async def start(self):
        app = self.get_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"[WS] Server listening on {self.host}:{self.port}")
