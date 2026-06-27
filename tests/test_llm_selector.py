from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from semantic_tool_router.llm_selector import (
    LLMSelector,
    _parse_tool_name,
    normalize_base_url,
)
from semantic_tool_router.models import DiscoveryResult, ToolSpec


@dataclass
class FakeChatClient:
    response: str

    def create_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, str] | None = None,
    ) -> str:
        _ = (model, messages, response_format)
        return self.response


class LLMSelectorTests(unittest.TestCase):
    def test_parse_tool_name_json(self) -> None:
        self.assertEqual(
            _parse_tool_name('{"tool":"search_files"}', ("search_files", "move_file")),
            "search_files",
        )

    def test_parse_tool_name_exact(self) -> None:
        self.assertEqual(
            _parse_tool_name("search_files", ("search_files", "move_file")), "search_files"
        )

    def test_parse_tool_name_hyphenated(self) -> None:
        self.assertEqual(
            _parse_tool_name('{"tool":"get-sum"}', ("get-sum", "echo")),
            "get-sum",
        )

    def test_normalize_base_url_rejects_oauth_callback(self) -> None:
        with self.assertRaises(ValueError):
            normalize_base_url(
                "https://api.chatanywhere.tech/v1/oauth/free/github/callback?code=abc"
            )

    def test_selector_uses_llm_response(self) -> None:
        candidates = (
            DiscoveryResult(
                tool=ToolSpec(name="move_file", description="Move a file"),
                score=0.9,
            ),
            DiscoveryResult(
                tool=ToolSpec(name="search_files", description="Search files recursively"),
                score=0.8,
            ),
        )
        selector = LLMSelector()
        selector.client = FakeChatClient('{"tool":"search_files"}')
        selected = selector.select("find python files recursively", candidates)
        self.assertEqual(selected, "search_files")

    def test_selector_does_not_cache_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache.json"
            cache_path.write_text(json.dumps({"bad": ""}), encoding="utf-8")
            selector = LLMSelector(cache_path=cache_path)
            selector.client = FakeChatClient("not-json")
            candidates = (
                DiscoveryResult(
                    tool=ToolSpec(name="echo", description="Echo text"),
                    score=1.0,
                ),
            )
            self.assertIsNone(selector.select("ping", candidates))
            self.assertEqual(selector._cache, {})


if __name__ == "__main__":
    unittest.main()
