"""SLUMBER scheduler: 24/7 autonomous operation mode."""
import asyncio
from datetime import datetime, timezone
from charles_hub.registry import AgentRegistry
from charles_hub.meeting import MeetingManager, MeetingType


class SlumberScheduler:
    """Night watch mode: periodic health checks, autonomous task execution."""

    def __init__(self, registry: AgentRegistry,
                 meeting_manager: MeetingManager,
                 interval: float = 300.0):
        self.registry = registry
        self.meeting_manager = meeting_manager
        self.interval = interval  # seconds between ticks
        self._running = False
        self._task: asyncio.Task | None = None

    async def _tick(self):
        """One slumber cycle."""
        now = datetime.now(timezone.utc).isoformat()
        print(f"[SLUMBER] tick at {now}")

        # Check all agent statuses
        for agent in self.registry.list_all():
            if self.registry.who_owns(agent.name) == "claude_code":
                if agent.status == "offline":
                    print(f"[SLUMBER] CC agent {agent.name} is offline")

        # Autonomous night watch: Hermes handles pending tasks
        if not self._has_active_meeting():
            self.meeting_manager.start_meeting(
                MeetingType.NIGHT_WATCH, "menxia",
                participants=[a.name for a in self.registry.list_by_owner("hermes")],
            )
            print("[SLUMBER] Night watch meeting started")

    def _has_active_meeting(self) -> bool:
        return self.meeting_manager.active_meeting is not None

    async def run(self):
        self._running = True
        print("[SLUMBER] Scheduler started")
        while self._running:
            await self._tick()
            await asyncio.sleep(self.interval)

    def start(self):
        self._task = asyncio.create_task(self.run())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        print("[SLUMBER] Scheduler stopped")

    async def pending_tasks_summary(self) -> str:
        """Generate summary of pending work for morning court."""
        agents = self.registry.list_all()
        offline_cc = [a for a in agents
                      if a.owner == "claude_code" and a.status == "offline"]
        online_hermes = [a for a in agents
                         if a.owner == "hermes" and a.status == "online"]
        lines = [
            "## 夜值摘要",
            f"- CC 离线 agent: {', '.join(a.display_name for a in offline_cc)}" if offline_cc else "- 所有 CC agent 在线",
            f"- Hermes 在线 agent: {', '.join(a.display_name for a in online_hermes)}",
            f"- 活跃会议: {'是' if self._has_active_meeting() else '否'}",
        ]
        return "\n".join(lines)
