from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

import httpx

from .models import ProviderResult


class ProviderError(RuntimeError):
    """A provider failed without exposing its response payload."""


class ProviderUnavailable(ProviderError):
    pass


class CompletionProvider(Protocol):
    name: str

    def complete(self, prompt: str, system_prompt: str | None, max_tokens: int) -> ProviderResult: ...

    def reachable(self) -> bool: ...


@dataclass
class DeterministicProvider:
    """Offline adapter used by tests and the credential-free demo."""

    name: str = "deterministic"
    response: str | None = None

    def complete(self, prompt: str, system_prompt: str | None, max_tokens: int) -> ProviderResult:
        text = self.response if self.response is not None else f"Safely processed: {prompt}"
        return ProviderResult(text=text, provider=self.name, token_usage=None)

    def reachable(self) -> bool:
        return True


@dataclass
class GroqProvider:
    api_key: str
    model: str = "llama-3.1-8b-instant"
    base_url: str = "https://api.groq.com/openai/v1"
    timeout_seconds: float = 20.0
    name: str = "groq"

    def complete(self, prompt: str, system_prompt: str | None, max_tokens: int) -> ProviderResult:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages, "max_tokens": max_tokens},
                timeout=self.timeout_seconds,
            )
            if response.status_code == 429 or response.status_code >= 500:
                raise ProviderUnavailable(f"{self.name} temporarily unavailable")
            response.raise_for_status()
            body = response.json()
            text = body["choices"][0]["message"]["content"]
            usage = body.get("usage", {}).get("total_tokens")
            return ProviderResult(text=str(text or ""), provider=self.name, token_usage=usage)
        except ProviderUnavailable:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProviderError(f"{self.name} returned an invalid response") from exc

    def reachable(self) -> bool:
        return bool(self.api_key)


@dataclass
class GeminiProvider:
    api_key: str
    model: str = "gemini-2.5-flash"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout_seconds: float = 20.0
    name: str = "gemini"

    def complete(self, prompt: str, system_prompt: str | None, max_tokens: int) -> ProviderResult:
        body: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens},
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        try:
            response = httpx.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json=body,
                timeout=self.timeout_seconds,
            )
            if response.status_code == 429 or response.status_code >= 500:
                raise ProviderUnavailable(f"{self.name} temporarily unavailable")
            response.raise_for_status()
            payload = response.json()
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            usage = payload.get("usageMetadata", {}).get("totalTokenCount")
            return ProviderResult(text=str(text or ""), provider=self.name, token_usage=usage)
        except ProviderUnavailable:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProviderError(f"{self.name} returned an invalid response") from exc

    def reachable(self) -> bool:
        return bool(self.api_key)


@dataclass
class FallbackProvider:
    primary: CompletionProvider
    fallback: CompletionProvider | None = None

    @property
    def name(self) -> str:
        return self.primary.name

    def complete(self, prompt: str, system_prompt: str | None, max_tokens: int) -> tuple[ProviderResult, bool]:
        try:
            return self.primary.complete(prompt, system_prompt, max_tokens), False
        except (ProviderUnavailable, ProviderError) as primary_error:
            if self.fallback is None:
                raise ProviderUnavailable("all configured providers are unavailable") from primary_error
            try:
                return self.fallback.complete(prompt, system_prompt, max_tokens), True
            except (ProviderUnavailable, ProviderError) as fallback_error:
                raise ProviderUnavailable("all configured providers are unavailable") from fallback_error

    def reachability(self) -> dict[str, bool]:
        values = {self.primary.name: self.primary.reachable()}
        if self.fallback:
            values[self.fallback.name] = self.fallback.reachable()
        return values
