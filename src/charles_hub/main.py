"""Charles Hub entry point. Wires all components together."""
import asyncio
import json
import signal
from charles_hub.config import config
from charles_hub.storage import Storage
from charles_hub.registry import AgentRegistry
from charles_hub.router import MessageRouter
from charles_hub.feishu_cli import FeishuCLI
from charles_hub.ws_server import CCWebSocketServer
from charles_hub.hermes_client import HermesClient
from charles_hub.meeting import MeetingManager
from charles_hub.slumber import SlumberScheduler


class CharlesHub:
    def __init__(self):
        self.storage = Storage(config.db_path)
        self.registry = AgentRegistry()
        self.router = MessageRouter(self.registry)
        self.feishu = FeishuCLI(config.feishu_cli_path)
        self.ws_server = CCWebSocketServer("0.0.0.0", config.port,
                                           self.storage, config)
        self.hermes = HermesClient(config.hermes_url)
        self.meetings = MeetingManager()
        self.slumber = SlumberScheduler(self.registry, self.meetings)
        self._running = False

    async def _process_message(self, raw_content: str, chat_id: str,
                               msg_id: str, sender: str):
        """Core message processing pipeline."""
        rm = self.router.parse(raw_content, chat_id, msg_id, sender)
        self.storage.save_message(msg_id, chat_id, sender,
                                  raw_content, rm.mentioned_bots)

        if rm.target_owner == "emperor":
            print(f"[HUB] Emperor message, broadcasting awareness")

        action = self.router.route_action(rm)

        if action == "ws_cc":
            await self.ws_server.send_to_cc({
                "type": "message",
                "from": sender,
                "chat_id": chat_id,
                "msg_id": msg_id,
                "content": rm.clean_content,
                "target_agent": rm.target_agent,
                "mentioned": True,
            })

        elif action == "http_hermes":
            result = await self.hermes.send_message(
                agent=rm.target_agent or "menxia",
                content=rm.clean_content,
                chat_id=chat_id,
                reply_to=msg_id,
            )
            if not result.success:
                print(f"[HUB] Hermes error: {result.error}")

        elif action == "hub_internal":
            await self._handle_internal(rm)

        else:  # broadcast
            self.meetings.add_message(sender, rm.clean_content)

    async def _handle_internal(self, rm):
        """Handle messages targeting Hub-managed bots (尚书省, 吏部, 工部)."""
        target = rm.target_agent
        if target == "shangshu":
            response = "尚书省收到，正在拆解任务..."
            await self._send_as_bot("shangshu", rm.chat_id, response)
        elif target == "libu":
            summary = self.registry.get_status_summary()
            await self._send_as_bot("libu", rm.chat_id,
                                    f"**吏部 · Agent 状态报表**\n\n{summary}")
        elif target == "gongbu":
            response = "工部收到，科研任务已入队列"
            await self._send_as_bot("gongbu", rm.chat_id, response)

    async def _send_as_bot(self, profile: str, chat_id: str, content: str):
        result = await self.feishu.send_markdown(profile, chat_id, content)
        if not result.success:
            print(f"[HUB] Failed to send as {profile}: {result.stderr}")

    async def _feishu_event_loop(self):
        """Listen for incoming Feishu messages via CLI event consume."""
        while self._running:
            try:
                proc = await self.feishu.listen_events("zhongshu")
                async for line in proc.stdout:
                    if not self._running:
                        break
                    try:
                        event = json.loads(line.decode("utf-8").strip())
                        header = event.get("header", {})
                        event_type = header.get("event_type", event.get("type", ""))
                        if event_type == "im.message.receive_v1":
                            evt = event.get("event", event)
                            msg = evt.get("message", {})
                            await self._process_message(
                                raw_content=json.dumps(msg.get("content", "{}")),
                                chat_id=msg.get("chat_id", evt.get("chat_id", "")),
                                msg_id=msg.get("message_id", ""),
                                sender=evt.get("sender", {}).get("sender_id", {}).get("open_id", "unknown"),
                            )
                    except json.JSONDecodeError:
                        pass
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[HUB] Feishu event error: {e}, reconnecting...")
                await asyncio.sleep(5)

    async def _cc_loop(self):
        """Poll for messages from Claude Code via WebSocket."""
        while self._running:
            msg = await self.ws_server.recv_from_cc()
            if msg and msg.get("type") == "send":
                profile_map = {"zhongshu": "zhongshu", "bingbu": "bingbu", "xingbu": "xingbu"}
                profile = profile_map.get(msg["bot"], "zhongshu")
                await self._send_as_bot(profile, msg["chat_id"], msg["content"])

    async def run(self):
        self._running = True
        print("[HUB] Charles Hub starting...")
        self.slumber.start()

        ws_task = asyncio.create_task(self.ws_server.start())

        async def on_cc_connect():
            await asyncio.sleep(1)
            await self.ws_server.send_resume()

        cc_resume_task = asyncio.create_task(on_cc_connect())
        cc_loop_task = asyncio.create_task(self._cc_loop())
        feishu_task = asyncio.create_task(self._feishu_event_loop())

        print("[HUB] Charles Hub running. Press Ctrl+C to stop.")

        try:
            await asyncio.gather(ws_task, cc_resume_task, cc_loop_task, feishu_task)
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            self.slumber.stop()
            await self.hermes.close()
            self.storage.close()
            print("[HUB] Charles Hub stopped.")


def main():
    hub = CharlesHub()
    loop = asyncio.new_event_loop()
    main_task = loop.create_task(hub.run())

    def shutdown():
        main_task.cancel()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    try:
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    main()
