from __future__ import annotations

from typing import Any

import httpx


class LLMClient:
    def __init__(self, api_key: str = "", model: str = "openai/gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._base_url = "https://openrouter.ai/api/v1/chat/completions"

    @property
    def is_real_available(self) -> bool:
        return bool(self.api_key)

    async def chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        if not self.api_key:
            return self._mock_response(system, user)

        try:
            return await self._real_chat(system, user, temperature)
        except Exception:
            return self._mock_response(system, user)

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

    def _mock_response(self, system: str, user: str) -> str:
        return (
            "[mock] Análisis basado en criterio GE. "
            "Señales detectadas: ownership, impacto cuantificable. "
            "Riesgos: título puede no reflejar responsabilidad real. "
            "Recomendación: validar con entrevista contextual."
        )
