"""吏部 (Ministry of Personnel): Agent registration, discovery, and status tracking."""
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class AgentInfo:
    name: str           # e.g. "zhongshu", "menxia", "bingbu"
    display_name: str   # e.g. "中书省", "门下省", "兵部"
    owner: str          # "claude_code" | "hermes" | "hub"
    status: str = "offline"
    capabilities: list[str] = field(default_factory=list)
    last_seen: str | None = None


class AgentRegistry:
    """吏部: central registry of all agents in the 三省六部 system."""

    AGENTS: dict[str, AgentInfo] = {
        "zhongshu":  AgentInfo("zhongshu",  "中书省", "claude_code",
                               capabilities=["drafting", "planning", "strategy"]),
        "menxia":    AgentInfo("menxia",    "门下省", "hermes",
                               capabilities=["review", "audit", "quality_gate"]),
        "shangshu":  AgentInfo("shangshu",  "尚书省", "hub",
                               capabilities=["task_decomposition", "dispatch", "tracking"]),
        "libu":      AgentInfo("libu",      "吏部",   "hub",
                               capabilities=["agent_discovery", "status_query"]),
        "hubu":      AgentInfo("hubu",      "户部",   "hermes",
                               capabilities=["data_storage", "file_management"]),
        "libu_docs": AgentInfo("libu_docs", "礼部",   "hermes",
                               capabilities=["feishu_docs", "knowledge_base"]),
        "bingbu":    AgentInfo("bingbu",    "兵部",   "claude_code",
                               capabilities=["code_execution", "deployment"]),
        "xingbu":    AgentInfo("xingbu",    "刑部",   "claude_code",
                               capabilities=["code_review", "security_audit"]),
        "gongbu":    AgentInfo("gongbu",    "工部",   "hub",
                               capabilities=["data_analysis", "modeling", "research"]),
    }

    def __init__(self):
        self._custom_agents: dict[str, AgentInfo] = {}

    def register(self, agent: AgentInfo):
        self._custom_agents[agent.name] = agent

    def get(self, name: str) -> AgentInfo | None:
        return self._custom_agents.get(name) or self.AGENTS.get(name)

    def list_all(self) -> list[AgentInfo]:
        all_agents = list(self.AGENTS.values())
        seen = set(a.name for a in all_agents)
        for custom in self._custom_agents.values():
            if custom.name not in seen:
                all_agents.append(custom)
        return all_agents

    def list_by_owner(self, owner: str) -> list[AgentInfo]:
        return [a for a in self.list_all() if a.owner == owner]

    def set_status(self, name: str, status: str):
        agent = self.get(name)
        if agent:
            agent.status = status
            agent.last_seen = datetime.now(timezone.utc).isoformat()

    def get_status_summary(self) -> str:
        lines = []
        for a in self.list_all():
            icon = {"online": "✅", "offline": "❌", "busy": "🔄"}.get(a.status, "❓")
            lines.append(f"{icon} {a.display_name}({a.name}): {a.status} [{a.owner}]")
        return "\n".join(lines)

    def who_owns(self, name: str) -> str:
        agent = self.get(name)
        return agent.owner if agent else "unknown"
