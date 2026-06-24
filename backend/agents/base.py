from agents.protocol import AgentEvent, AgentResult, Decision
from agents.memory import AgentMemory
from services import ai_client

MAX_REACT_STEPS = 4


class BaseAgent:
    role: str = "agent"
    system_prompt: str = ""

    def __init__(self, skills: dict):
        self.skills = skills

    async def run(self, event: AgentEvent) -> AgentResult:
        memory = AgentMemory(event.user_id)
        recent = await memory.get_recent(3)
        episodes = await memory.get_episodes(2)

        observations = []
        all_skill_results = {}
        final_notification = None
        final_follow_ups = []
        decision = Decision(reasoning="")
        usage = {}

        for step in range(MAX_REACT_STEPS):
            # 每步开始前检查上下文占用，超50%压缩记忆
            if step > 0 and usage.get("context_ratio", 0) >= 0.5:
                print(f"[Token] {self.role} step={step} context={usage['context_ratio']:.1%} → compressing memory")
                await memory.maybe_compress(usage["context_ratio"])
                recent = await memory.get_recent(3)  # 刷新压缩后的记忆

            prompt = self._build_react_prompt(event, recent, episodes, observations)
            for attempt in range(2):
                raw, usage = await ai_client.chat_with_usage(prompt, system=self.system_prompt)
                decision = Decision.parse(raw)
                if not decision._parse_failed:
                    break
                print(f"[WARN] {self.role} step={step} parse retry {attempt + 1}")

            if usage.get("context_ratio", 0) > 0:
                print(f"[Token] {self.role} step={step} context={usage['context_ratio']:.1%} ({usage.get('prompt_tokens', 0)}/{ai_client.context_window})")

            if decision.should_notify_user:
                final_notification = decision.notification_content
            final_follow_ups = decision.follow_up_events

            if not decision.skill_calls:
                break

            step_results = {}
            for call in decision.skill_calls:
                skill_name = call.get("name", "")
                params = call.get("params", {})
                if skill_name in self.skills:
                    result = await self.skills[skill_name](event.user_id, params)
                    step_results[skill_name] = result
                    all_skill_results[skill_name] = result

            observations.append({
                "step": step,
                "thought": decision.reasoning,
                "skills_called": list(step_results.keys()),
                "results": step_results,
            })

        if decision.reasoning and decision.reasoning != "parse_failed":
            await memory.add_short_term("reasoning", self.role, decision.reasoning)

        return AgentResult(
            data=all_skill_results,
            follow_up_events=final_follow_ups,
            notification=final_notification,
        )

    def _build_react_prompt(self, event: AgentEvent, recent, episodes, observations: list) -> str:
        skills_list = list(self.skills.keys())
        obs_text = f"\n已执行步骤观察：{observations}" if observations else ""
        step_hint = "请继续下一步。" if observations else "请决定第一步操作。"
        return f"""你是一食万象的{self.role}。

当前事件：{event.event_type}
事件数据：{event.data}
最近记忆：{recent}
情节记忆：{episodes}
可用Skills：{skills_list}{obs_text}

{step_hint}任务完成时返回 skill_calls 为空列表。
返回纯JSON（禁止markdown包裹）：
{{
    "reasoning": "当前思考",
    "skill_calls": [{{"name": "skill名", "params": {{}}}}],
    "should_notify_user": false,
    "notification_content": "",
    "follow_up_events": []
}}"""
