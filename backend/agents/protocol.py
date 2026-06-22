from dataclasses import dataclass, field
from typing import Any, Optional
import json


@dataclass
class InterAgentMessage:
    from_agent: str
    to_agent: str
    intent: str
    payload: dict
    correlation_id: str = ""


@dataclass
class AgentEvent:
    event_type: str
    user_id: str
    data: dict = field(default_factory=dict)


@dataclass
class Decision:
    reasoning: str
    skill_calls: list[dict] = field(default_factory=list)
    should_notify_user: bool = False
    notification_content: str = ""
    follow_up_events: list[dict] = field(default_factory=list)
    _parse_failed: bool = False

    @classmethod
    def parse(cls, raw: str) -> "Decision":
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            d = json.loads(text)
            return cls(
                reasoning=d.get("reasoning", ""),
                skill_calls=d.get("skill_calls", []),
                should_notify_user=d.get("should_notify_user", False),
                notification_content=d.get("notification_content", ""),
                follow_up_events=d.get("follow_up_events", []),
            )
        except Exception as e:
            print(f"[WARN] Decision.parse failed: {e}\nraw={raw[:200]}")
            return cls(reasoning="parse_failed", skill_calls=[], _parse_failed=True)


@dataclass
class AgentResult:
    data: Any = None
    follow_up_events: list[dict] = field(default_factory=list)
    notification: Optional[str] = None
