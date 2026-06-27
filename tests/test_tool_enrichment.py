from __future__ import annotations

import unittest

from semantic_tool_router.models import ToolSpec
from semantic_tool_router.tool_enrichment import enrich_tool_spec, enrichment_phrases


class ToolEnrichmentTests(unittest.TestCase):
    def test_create_relations_gets_link_phrases(self) -> None:
        phrases = enrichment_phrases("create_relations")
        self.assertTrue(any("link" in phrase for phrase in phrases))

    def test_enrich_adds_examples(self) -> None:
        tool = ToolSpec(name="create_relations", description="Create relations between entities")
        enriched = enrich_tool_spec(tool)
        self.assertGreater(len(enriched.examples), 0)
        self.assertIn("connect a project to a research topic", enriched.examples)


if __name__ == "__main__":
    unittest.main()
