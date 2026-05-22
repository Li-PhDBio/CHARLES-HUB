"""Meeting state machine: 议题→讨论→决议→纪要."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class MeetingPhase(Enum):
    IDLE = "idle"
    TOPIC = "topic"
    DISCUSSION = "discussion"
    DECISION = "decision"
    MINUTES = "minutes"


class MeetingType(Enum):
    MORNING_COURT = "早朝"
    DEPARTMENT_MEETING = "部议"
    IMPERIAL_COUNCIL = "御前会议"
    NIGHT_WATCH = "夜值"


@dataclass
class Meeting:
    meeting_type: MeetingType
    host: str
    phase: MeetingPhase = MeetingPhase.IDLE
    topic: str | None = None
    participants: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    minutes: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    closed_at: str | None = None

    def open(self, topic: str):
        self.topic = topic
        self.phase = MeetingPhase.TOPIC

    def discuss(self, participant: str, message: str):
        if self.phase in (MeetingPhase.TOPIC, MeetingPhase.DISCUSSION):
            self.phase = MeetingPhase.DISCUSSION
            self.minutes.append(f"[{participant}]: {message}")

    def decide(self, decision: str):
        self.phase = MeetingPhase.DECISION
        self.decisions.append(decision)
        self.minutes.append(f"[决议]: {decision}")

    def conclude(self) -> str:
        self.phase = MeetingPhase.MINUTES
        self.closed_at = datetime.now(timezone.utc).isoformat()
        lines = [
            f"## {self.meeting_type.value} 会议纪要",
            f"- 主持人: {self.host}",
            f"- 议题: {self.topic}",
            f"- 参与者: {', '.join(self.participants)}",
            f"- 开始: {self.started_at}",
            f"- 结束: {self.closed_at}",
            "",
            "### 讨论记录",
            *[f"- {m}" for m in self.minutes],
            "",
            "### 决议",
            *[f"- {d}" for d in self.decisions],
        ]
        summary = "\n".join(lines)
        self.minutes.append(summary)
        return summary


class MeetingManager:
    def __init__(self):
        self._active: Meeting | None = None
        self._history: list[Meeting] = []

    @property
    def active_meeting(self) -> Meeting | None:
        return self._active

    def start_meeting(self, meeting_type: MeetingType, host: str,
                      participants: list[str] | None = None) -> Meeting:
        if self._active:
            self._active.conclude()
            self._history.append(self._active)
        self._active = Meeting(
            meeting_type=meeting_type,
            host=host,
            participants=participants or [],
        )
        return self._active

    def end_meeting(self) -> str | None:
        if not self._active:
            return None
        summary = self._active.conclude()
        self._history.append(self._active)
        self._active = None
        return summary

    def add_message(self, participant: str, message: str):
        if self._active:
            self._active.discuss(participant, message)

    def add_decision(self, decision: str):
        if self._active:
            self._active.decide(decision)
