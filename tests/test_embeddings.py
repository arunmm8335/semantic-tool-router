from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from semantic_tool_router.embeddings import (
    HashingEmbeddingProvider,
    OpenAIEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)


class EmbeddingsTests(unittest.TestCase):
    def test_hashing_embedding_provider(self) -> None:
        provider = HashingEmbeddingProvider(dimensions=128)
        vector = provider.embed("hello world")
        self.assertEqual(len(vector), 128)
        self.assertTrue(all(isinstance(x, float) for x in vector))

        # Check normalization (magnitude close to 1)
        magnitude = sum(x * x for x in vector)
        self.assertAlmostEqual(magnitude, 1.0, places=5)

    def test_sentence_transformer_missing_dependency(self) -> None:
        # Hide sentence-transformers from sys.modules to simulate missing dependency
        with patch.dict("sys.modules", {"sentence_transformers": None}):
            with self.assertRaisesRegex(ImportError, "sentence-transformers is required"):
                SentenceTransformerEmbeddingProvider()

    def test_sentence_transformer_mocked(self) -> None:
        mock_model = MagicMock()

        # We simulate the returned array as a helper class that has tolist()
        class FakeArray:
            def tolist(self) -> list[float]:
                return [0.1, 0.2, 0.3]

        mock_model.encode.return_value = FakeArray()

        # Create a mock SentenceTransformer class
        mock_st_class = MagicMock(return_value=mock_model)

        # Create a dummy module to mock sentence_transformers
        mock_module = MagicMock()
        mock_module.SentenceTransformer = mock_st_class

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            provider = SentenceTransformerEmbeddingProvider()
            vector = provider.embed("test text")

        self.assertEqual(vector, [0.1, 0.2, 0.3])
        mock_model.encode.assert_called_once_with("test text", convert_to_numpy=True)

    def test_openai_missing_dependency(self) -> None:
        # Hide openai from sys.modules to simulate missing dependency
        with patch.dict("sys.modules", {"openai": None}):
            with self.assertRaisesRegex(ImportError, "openai is required"):
                OpenAIEmbeddingProvider()

    def test_openai_mocked(self) -> None:
        mock_client = MagicMock()

        mock_embedding_data = MagicMock()
        mock_embedding_data.embedding = [0.5, 0.6, 0.7]

        mock_response = MagicMock()
        mock_response.data = [mock_embedding_data]

        mock_client.embeddings.create.return_value = mock_response

        # Create a mock OpenAI class
        mock_openai_class = MagicMock(return_value=mock_client)

        # Create a dummy module to mock openai
        mock_module = MagicMock()
        mock_module.OpenAI = mock_openai_class

        with patch.dict("sys.modules", {"openai": mock_module}):
            provider = OpenAIEmbeddingProvider(api_key="fake-key")
            vector = provider.embed("test query")

        self.assertEqual(vector, [0.5, 0.6, 0.7])
        mock_client.embeddings.create.assert_called_once_with(
            input=["test query"],
            model="text-embedding-3-small",
        )


if __name__ == "__main__":
    unittest.main()
