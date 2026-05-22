"""三省六部 message router: routes incoming Feishu messages to the correct agent."""
import re
from dataclasses import dataclass, field
from charles_hub.registry import AgentRegistry

MENTION_PATTERN = re.compile(r"@(\S+?)(?:\s|$)")


@dataclass
class RoutedMessage:
    raw_content: str
    chat_id: str
    msg_id: str
    sender: str
    mentioned_bots: list[str] = field(default_factory=list)
    target_agent: str | None = None
    target_owner: str | None = None
    is_public: bool = True

    @property
    def clean_content(self) -> str:
        """Content with @mentions stripped."""
        c = self.raw_content
        for bot in self.mentioned_bots:
            c = c.replace(f"@{bot}", "").strip()
        return c


class MessageRouter:
    """Routes messages per the 三省六部 routing rules."""

    def __init__(self, registry: AgentRegistry | None = None):
        self.registry = registry or AgentRegistry()

    def _resolve_name(self, mention: str) -> str | None:
        """Resolve a mention (agent name or display name) to agent name."""
        if self.registry.get(mention):
            return mention
        for agent in self.registry.list_all():
            if agent.display_name == mention:
                return agent.name
        return None

    def parse(self, raw_content: str, chat_id: str, msg_id: str,
              sender: str) -> RoutedMessage:
        mentioned = MENTION_PATTERN.findall(raw_content)
        known_bots = [m for m in mentioned if self._resolve_name(m)]
        rm = RoutedMessage(
            raw_content=raw_content,
            chat_id=chat_id,
            msg_id=msg_id,
            sender=sender,
            mentioned_bots=known_bots,
        )

        if sender == "emperor" or "皇帝" in raw_content:
            rm.target_agent = None
            rm.target_owner = "emperor"
            return rm

        if known_bots:
            primary_target = self._resolve_name(known_bots[0])
            rm.target_agent = primary_target
            rm.target_owner = self.registry.who_owns(primary_target) if primary_target else None
        else:
            rm.target_agent = None
            rm.target_owner = None

        return rm

    def route_action(self, rm: RoutedMessage) -> str:
        """Return routing action: 'ws_cc' | 'http_hermes' | 'hub_internal' | 'broadcast'."""
        if rm.target_owner == "claude_code":
            return "ws_cc"
        elif rm.target_owner == "hermes":
            return "http_hermes"
        elif rm.target_owner == "hub":
            return "hub_internal"
        else:
            return "broadcast"
