import httpx
import json
from config import ai_config

MODEL_CONTEXT_WINDOWS = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-3.5-turbo": 16385,
    "GPT-5.5": 200000,
    "claude-3-5-sonnet": 200000,
    "claude-3-opus": 200000,
}
DEFAULT_CONTEXT_WINDOW = 128000


class AIClient:
    """统一 AI 模型调用封装"""

    def __init__(self):
        self.base_url = ai_config.base_url
        self.api_key = ai_config.api_key
        self.model = ai_config.model_name
        self.client = httpx.AsyncClient(timeout=60.0)

    @property
    def context_window(self) -> int:
        return MODEL_CONTEXT_WINDOWS.get(self.model, DEFAULT_CONTEXT_WINDOW)

    async def chat(self, prompt: str, system: str = "") -> str:
        content, _ = await self.chat_with_usage(prompt, system)
        return content

    async def chat_with_usage(self, prompt: str, system: str = "") -> tuple:
        """返回 (content, usage)，usage 含 prompt_tokens/context_ratio"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": messages, "max_tokens": 2000},
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        usage["context_ratio"] = usage.get("prompt_tokens", 0) / self.context_window
        return content, usage

    async def vision(self, image_base64: str, prompt: str, mime_type: str = "image/jpeg") -> str:
        messages = [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}}
        ]}]
        resp = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": messages, "max_tokens": 4000},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def close(self):
        await self.client.aclose()


ai_client = AIClient()
