from __future__ import annotations

import asyncio

import httpx


class LLMClient:
    def __init__(self, api_key: str = "", model: str = ""):
        from core.config import settings
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.openrouter_model or "openai/gpt-4o-mini"
        self._base_url = "https://openrouter.ai/api/v1/chat/completions"

    @property
    def is_real_available(self) -> bool:
        return bool(self.api_key)

    async def chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        if not self.api_key:
            raise RuntimeError("LLMClient: no API key configured")

        return await self._real_chat(system, user, temperature)

    async def classify(self, text: str, categories: list[str]) -> str:
        prompt = (
            f"Clasificá el siguiente texto en UNA de estas categorías: "
            f"{', '.join(categories)}.\n\nTexto: {text}\n\nCategoría:"
        )
        return await self.chat(
            "Sos un asistente que clasifica texto. Respondé solo con la categoría.",
            prompt,
            temperature=0.1,
        )

    async def summarize(self, text: str, max_words: int = 100) -> str:
        prompt = f"Resumí el siguiente texto en máximo {max_words} palabras:\n\n{text}"
        return await self.chat(
            "Sos un asistente que resume texto de forma concisa.",
            prompt,
        )

    def complete(self, prompt: str, temperature: float = 0.3) -> str:
        """Sync single-prompt completion."""
        return self._run(self.chat("Sos un asistente útil y conciso.", prompt, temperature))

    def chat_messages(self, system: str, messages: list[dict], temperature: float = 0.4) -> str:
        """Sync multi-turn chat with a list of {'role', 'content'} messages."""
        return self._run(self._real_chat_messages(system, messages, temperature))

    @staticmethod
    def _run(coro):
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            return asyncio.run(coro)

    async def _real_chat_messages(self, system: str, messages: list[dict], temperature: float) -> str:
        if not self.api_key:
            raise RuntimeError("LLMClient: no API key configured")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}] + messages,
            "temperature": temperature,
            "max_tokens": 500,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(self._base_url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
        choices = data.get("choices", [])
        return choices[0].get("message", {}).get("content", "") if choices else ""

    async def _real_chat(self, system: str, user: str, temperature: float) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": 500,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(self._base_url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""


