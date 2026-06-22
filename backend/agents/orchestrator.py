from agents.protocol import AgentEvent, AgentResult
from agents.agents import TasteAgent, SocialAgent, CityAgent

# Event type to agent mapping
EVENT_ROUTING = {
    "meal.uploaded": ["taste"],
    "report.weekly": ["taste"],
    "match.discover": ["social"],
    "match.mutual": ["social", "taste"],
    "city.heatmap": ["city"],
    "city.trends": ["city"],
    "city.recommend": ["city", "taste"],
    "user.feedback": ["taste"],
}


class Orchestrator:
    def __init__(self, skills: dict):
        self.taste_agent = TasteAgent(skills.get("taste", {}))
        self.social_agent = SocialAgent(skills.get("social", {}))
        self.city_agent = CityAgent(skills.get("city", {}))
        self.agent_map = {
            "taste": self.taste_agent,
            "social": self.social_agent,
            "city": self.city_agent,
        }

    async def process_event(self, event: AgentEvent) -> AgentResult:
        agent_keys = EVENT_ROUTING.get(event.event_type, ["taste"])

        all_results = {}
        all_follow_ups = []
        trace = []
        notification = None

        for key in agent_keys:
            agent = self.agent_map[key]
            result = await agent.run(event)
            all_results[key] = result.data
            all_follow_ups.extend(result.follow_up_events)
            trace.append({
                "event_type": event.event_type,
                "agent": key,
                "skills": list(result.data.keys()) if isinstance(result.data, dict) else [],
                "follow_up_count": len(result.follow_up_events),
            })
            if result.notification:
                notification = result.notification

        # Process follow-up events (one level deep to avoid infinite loops)
        for follow_up in all_follow_ups[:3]:
            fu_event = AgentEvent(
                event_type=follow_up.get("type", ""),
                user_id=event.user_id,
                data=follow_up
            )
            fu_keys = EVENT_ROUTING.get(fu_event.event_type, [])
            for key in fu_keys:
                agent = self.agent_map.get(key)
                if agent:
                    fu_result = await agent.run(fu_event)
                    all_results[f"follow_up_{key}"] = fu_result.data
                    trace.append({
                        "event_type": fu_event.event_type,
                        "agent": key,
                        "skills": list(fu_result.data.keys()) if isinstance(fu_result.data, dict) else [],
                        "follow_up_count": len(fu_result.follow_up_events),
                    })

        all_results["__trace"] = trace
        return AgentResult(
            data=all_results,
            follow_up_events=all_follow_ups,
            notification=notification
        )
