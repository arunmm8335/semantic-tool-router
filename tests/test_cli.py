from __future__ import annotations

import argparse
import unittest

from semantic_tool_router.cli import apply_profile


class ProfileTests(unittest.TestCase):
    def test_quality_profile_sets_embedder_and_reranker(self) -> None:
        args = argparse.Namespace(
            profile="quality",
            embedder="hashing",
            embedding_model=None,
            reranker="none",
        )
        apply_profile(args)
        self.assertEqual(args.embedder, "sentence-transformers")
        self.assertEqual(args.embedding_model, "all-MiniLM-L6-v2")
        self.assertEqual(args.reranker, "cross-encoder")

    def test_fast_profile_leaves_defaults(self) -> None:
        args = argparse.Namespace(
            profile="fast",
            embedder="hashing",
            embedding_model=None,
            reranker="none",
        )
        apply_profile(args)
        self.assertEqual(args.embedder, "hashing")
        self.assertIsNone(args.embedding_model)
        self.assertEqual(args.reranker, "none")


if __name__ == "__main__":
    unittest.main()
