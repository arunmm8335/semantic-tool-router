from __future__ import annotations

import argparse
import unittest

from semantic_tool_router.cli import apply_profile, resolve_hybrid_weight


class ProfileTests(unittest.TestCase):
    def test_quality_profile_sets_embedder_and_reranker(self) -> None:
        args = argparse.Namespace(
            profile="quality",
            embedder="hashing",
            embedding_model=None,
            reranker="none",
            hybrid_weight=None,
        )
        apply_profile(args)
        self.assertEqual(args.embedder, "sentence-transformers")
        self.assertEqual(args.embedding_model, "all-MiniLM-L6-v2")
        self.assertEqual(args.reranker, "cross-encoder")
        self.assertEqual(resolve_hybrid_weight(args), 0.0)

    def test_fast_profile_leaves_defaults(self) -> None:
        args = argparse.Namespace(
            profile="fast",
            embedder="hashing",
            embedding_model=None,
            reranker="none",
            hybrid_weight=None,
        )
        apply_profile(args)
        self.assertEqual(args.embedder, "hashing")
        self.assertIsNone(args.embedding_model)
        self.assertEqual(args.reranker, "none")
        self.assertEqual(resolve_hybrid_weight(args), 0.4)

    def test_explicit_hybrid_weight_overrides_profile_default(self) -> None:
        args = argparse.Namespace(
            profile="quality",
            embedder="sentence-transformers",
            embedding_model="all-MiniLM-L6-v2",
            reranker="cross-encoder",
            hybrid_weight=0.25,
        )
        self.assertEqual(resolve_hybrid_weight(args), 0.25)

    def test_bge_profile(self) -> None:
        args = argparse.Namespace(
            profile="bge",
            embedder="hashing",
            embedding_model=None,
            reranker="none",
            hybrid_weight=None,
        )
        apply_profile(args)
        self.assertEqual(args.embedder, "sentence-transformers")
        self.assertEqual(args.embedding_model, "BAAI/bge-small-en-v1.5")
        self.assertEqual(args.reranker, "none")
        self.assertEqual(resolve_hybrid_weight(args), 0.0)


if __name__ == "__main__":
    unittest.main()
