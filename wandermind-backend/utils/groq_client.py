import asyncio
import json
import re
from typing import Any, Dict, Iterable, List, Optional

from groq import AsyncGroq

from config import settings


class GroqClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self.client = AsyncGroq(api_key=self.api_key) if self.api_key else None

    @property
    def enabled(self) -> bool:
        return self.client is not None

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2,
    ) -> str:
        if not self.client:
            raise RuntimeError("GROQ_API_KEY is missing. Add it to .env.")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        delays = [2, 4, 8]
        last_error: Optional[Exception] = None

        for attempt in range(len(delays) + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens or settings.max_groq_output_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:  # pragma: no cover - external API dependent
                last_error = exc
                if not self._is_rate_limit(exc) or attempt >= len(delays):
                    break
                await asyncio.sleep(delays[attempt])

        raise RuntimeError(f"Groq request failed after retries: {last_error}")

    async def json_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        raw = await self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.0,
        )
        parsed = self._try_parse_json(raw)
        if parsed is not None:
            return parsed

        strict_prompt = (
            "Return ONLY valid JSON. No markdown, no comments, no explanations.\n"
            f"Original task:\n{user_prompt}"
        )
        raw_retry = await self.chat(
            system_prompt=system_prompt,
            user_prompt=strict_prompt,
            max_tokens=max_tokens,
            temperature=0.0,
        )
        parsed_retry = self._try_parse_json(raw_retry)
        if parsed_retry is not None:
            return parsed_retry
        raise ValueError("Groq JSON parse failure after one retry")

    def _is_rate_limit(self, exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None)
        if status_code == 429:
            return True
        message = str(exc).lower()
        return "429" in message or "rate" in message and "limit" in message

    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Extract the first JSON object/array from model output.
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


async def run_batched_json_extractions(
    groq_client: GroqClient,
    texts: Iterable[str],
    batch_size: int = 5,
) -> List[Dict[str, Any]]:
    text_list = list(texts)
    results: List[Dict[str, Any]] = []

    for i in range(0, len(text_list), batch_size):
        batch = text_list[i : i + batch_size]
        calls = [
            groq_client.json_chat(
                system_prompt="You are a travel data extraction assistant.",
                user_prompt=(
                    "Extract structured travel facts from the following traveler text. "
                    "Return ONLY a JSON object with these keys: "
                    "places_mentioned, food_tips, transport_tips, hidden_gems, "
                    "warnings, estimated_costs, best_time_tips. "
                    "Each key maps to a list of strings. If none found, use empty list. "
                    f"Text: {text[: settings.max_groq_input_chars]}"
                ),
            )
            for text in batch
        ]

        settled = await asyncio.gather(*calls, return_exceptions=True)
        for item in settled:
            if isinstance(item, Exception):
                results.append(
                    {
                        "places_mentioned": [],
                        "food_tips": [],
                        "transport_tips": [],
                        "hidden_gems": [],
                        "warnings": [],
                        "estimated_costs": [],
                        "best_time_tips": [],
                    }
                )
            else:
                results.append(item)

    return results
