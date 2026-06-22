import httpx
import json
from config import ai_config


class AIClient:
    """统一 AI 模型调用封装"""

    def __init__(self):
        self.base_url = ai_config.base_url
        self.api_key = ai_config.api_key
        self.model = ai_config.model_name
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat(self, prompt: str, system: str = "") -> str:
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
        return resp.json()["choices"][0]["message"]["content"]

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
