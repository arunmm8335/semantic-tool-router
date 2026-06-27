from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from semantic_tool_router.models import DiscoveryResult

TOOL_NAME_RE = re.compile(r"[a-zA-Z0-9_-]+")


class ChatClient(Protocol):
    def create_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, str] | None = None,
    ) -> str: ...


@dataclass
class LLMSelector:
    """Agent that asks an OpenAI-compatible chat model to pick one retrieved tool."""

    model: str = "gpt-4o-mini"
    api_key: str | None = None
    base_url: str | None = None
    cache_path: Path | None = None
    temperature: float = 0.0
    verbose: bool = False
    _cache: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _client: ChatClient | None = field(default=None, init=False, repr=False)
    last_error: str | None = field(default=None, init=False, repr=False)
    error_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.base_url = normalize_base_url(self.base_url or os.environ.get("OPENAI_BASE_URL"))
        if self.cache_path is not None:
            self._load_cache()

    def select(self, query: str, candidates: tuple[DiscoveryResult, ...]) -> str | None:
        if not candidates:
            return None

        names = tuple(item.tool.name for item in candidates)
        cache_key = self._cache_key(query, names)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return cached if cached in names else None

        prompt = _format_prompt(query, candidates)
        try:
            raw = self.client.create_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
        except Exception as error:
            self._record_error(error)
            return None

        selected = _parse_tool_name(raw, names)
        if selected is None:
            self._record_error(ValueError(f"Could not parse tool name from LLM response: {raw!r}"))
            return None

        self._cache[cache_key] = selected
        if self.cache_path is not None:
            self._save_cache()
        return selected

    def verify_connection(self) -> None:
        allowed = ("echo_probe",)
        probe = self.client.create_completion(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "User request: ping\n\n"
                        "Candidate tools:\n"
                        "1. echo_probe: echo back a ping\n\n"
                        "Allowed tool names: echo_probe\n"
                        'Return JSON like {"tool":"echo_probe"}.'
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        parsed = _parse_tool_name(probe, allowed)
        if parsed not in allowed:
            raise ValueError(
                "LLM connection probe failed: model did not return a valid tool name. "
                f"Response was: {probe!r}"
            )

    @property
    def client(self) -> ChatClient:
        if self._client is None:
            self._client = _build_openai_client(
                api_key=self.api_key or os.environ.get("OPENAI_API_KEY"),
                base_url=self.base_url,
                temperature=self.temperature,
            )
        return self._client

    @client.setter
    def client(self, value: ChatClient) -> None:
        self._client = value

    def _record_error(self, error: Exception) -> None:
        self.error_count += 1
        message = str(error).strip() or error.__class__.__name__
        if self.last_error is None:
            self.last_error = message
        if self.verbose or self.error_count == 1:
            print(f"LLM selection failed: {message}", file=sys.stderr)

    def _cache_key(self, query: str, names: tuple[str, ...]) -> str:
        payload = json.dumps({"query": query, "tools": names}, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _load_cache(self) -> None:
        if self.cache_path is None or not self.cache_path.exists():
            return
        data = json.loads(self.cache_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            self._cache = {
                str(key): str(value)
                for key, value in data.items()
                if isinstance(value, str) and value
            }

    def _save_cache(self) -> None:
        if self.cache_path is None:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(self._cache, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


_SYSTEM_PROMPT = (
    "You choose exactly one tool from the candidate list to fulfill the user request. "
    'Respond with JSON only, using this schema: {"tool":"<exact_tool_name>"}. '
    "The tool name must match one candidate exactly."
)


def normalize_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    cleaned = base_url.strip().rstrip("/")
    if "/oauth/" in cleaned or "callback" in cleaned:
        raise ValueError(
            "OPENAI_BASE_URL looks like an OAuth callback URL, not an API endpoint. "
            "Use the provider's API root, for example: https://api.chatanywhere.tech/v1"
        )
    if cleaned.endswith("/v1/oauth") or cleaned.endswith("/oauth"):
        raise ValueError(
            "OPENAI_BASE_URL must point to the chat completions API root "
            "(usually ending in /v1), not an OAuth path."
        )
    return cleaned


def _format_prompt(query: str, candidates: tuple[DiscoveryResult, ...]) -> str:
    allowed = [item.tool.name for item in candidates]
    lines = [
        f"User request: {query}",
        "",
        "Candidate tools:",
    ]
    for index, item in enumerate(candidates, start=1):
        description = item.tool.description.strip() or "(no description)"
        lines.append(f"{index}. {item.tool.name}: {description}")
    lines.extend(
        [
            "",
            f"Allowed tool names: {', '.join(allowed)}",
            'Return JSON like {"tool":"<name>"}.',
        ]
    )
    return "\n".join(lines)


def _parse_tool_name(raw: str, names: tuple[str, ...]) -> str | None:
    text = raw.strip()
    if not text:
        return None

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        for key in ("tool", "tool_name", "name"):
            value = payload.get(key)
            if isinstance(value, str) and value in names:
                return value

    stripped = text.strip().strip("`\"'")
    if stripped in names:
        return stripped

    for name in sorted(names, key=len, reverse=True):
        if name in stripped:
            return name

    for match in TOOL_NAME_RE.finditer(stripped):
        token = match.group(0)
        if token in names:
            return token
    return None


@dataclass
class _OpenAIChatClient:
    api_key: str
    base_url: str | None
    temperature: float

    def create_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, str] | None = None,
    ) -> str:
        try:
            import openai
        except ImportError as error:
            raise ImportError(
                "openai is required for --selector llm. "
                "Install it with `pip install semantic-tool-router[openai]`"
            ) from error

        client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        kwargs: dict[str, object] = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        try:
            response = client.chat.completions.create(**kwargs)  # type: ignore[call-overload]
        except Exception as error:
            endpoint = self.base_url or "https://api.openai.com/v1"
            raise RuntimeError(
                f"{error.__class__.__name__} calling {endpoint} with model {model!r}: {error}"
            ) from error

        message = response.choices[0].message.content
        if not message:
            raise ValueError("LLM returned an empty response")
        return str(message)


def _build_openai_client(
    *,
    api_key: str | None,
    base_url: str | None,
    temperature: float,
) -> ChatClient:
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for --selector llm (or pass --openai-api-key)")
    return _OpenAIChatClient(api_key=api_key, base_url=base_url, temperature=temperature)


def build_llm_selector(
    *,
    model: str,
    api_key: str | None,
    base_url: str | None,
    cache_path: str | Path | None,
    verbose: bool = False,
    verify: bool = True,
) -> LLMSelector:
    selector = LLMSelector(
        model=model,
        api_key=api_key,
        base_url=base_url,
        cache_path=Path(cache_path) if cache_path else None,
        verbose=verbose,
    )
    _ = selector.client
    if verify:
        selector.verify_connection()
    return selector
