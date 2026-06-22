from agents.protocol import AgentEvent, AgentResult, Decision
from agents.memory import AgentMemory
from services import ai_client


class BaseAgent:
    role: str = "agent"
    system_prompt: str = ""

    def __init__(self, skills: dict):
        self.skills = skills

    async def run(self, event: AgentEvent) -> AgentResult:
        memory = AgentMemory(event.user_id)
        perception = await self.perceive(event)
        decision = await self.reason(perception, memory, event)
        result = await self.act(decision, event)
        await self.reflect(result, decision, memory)
        return AgentResult(
            data=result,
            follow_up_events=decision.follow_up_events,
            notification=decision.notification_content if decision.should_notify_user else None
        )

    async def perceive(self, event: AgentEvent) -> dict:
        return {"event_type": event.event_type, "data": event.data}

    async def reason(self, perception: dict, memory: AgentMemory, event: AgentEvent) -> Decision:
        recent = await memory.get_recent(3)
        episodes = await memory.get_episodes(2)
        feedback = await memory.get_feedback_summary()

        skills_list = list(self.skills.keys())
        prompt = f"""你是一食万象的{self.role}。基于当前感知和记忆，决定需要执行哪些操作。

当前事件：{event.event_type}
事件数据：{perception['data']}
最近记忆：{recent}
情节记忆：{episodes}
反馈历史：{feedback}
可用Skills：{skills_list}

请返回JSON：
{{
    "reasoning": "你的思考过程",
    "skill_calls": [{{"name": "skill名", "params": {{}}}}],
    "should_notify_user": true/false,
    "notification_content": "如果需要通知用户的内容",
    "follow_up_events": [{{"type": "事件类型", "reason": "触发原因"}}]
}}"""
        raw = await ai_client.chat(prompt, system=self.system_prompt)
        return Decision.parse(raw)

    async def act(self, decision: Decision, event: AgentEvent) -> dict:
        results = {}
        for call in decision.skill_calls:
            skill_name = call.get("name", "")
            params = call.get("params", {})
            if skill_name in self.skills:
                skill_fn = self.skills[skill_name]
                result = await skill_fn(event.user_id, params)
                results[skill_name] = result
        return results

    async def reflect(self, result: dict, decision: Decision, memory: AgentMemory):
        if decision.reasoning:
            await memory.add_short_term("reasoning", self.role, decision.reasoning)
