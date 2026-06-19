from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Protocol


TOKEN_RE = re.compile(r"[a-zA-Z0-9_./:-]+")


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class HashingEmbeddingProvider:
    """Small local embedder for repeatable MVP retrieval without external services."""

    def __init__(self, dimensions: int = 384) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = _tokens(text)
        counts = Counter(tokens)

        for token, count in counts.items():
            index = _stable_index(token, self.dimensions)
            sign = -1.0 if _stable_index(f"{token}:sign", 2) == 0 else 1.0
            vector[index] += sign * (1.0 + math.log(count))

        return _normalize(vector)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have equal dimensions")
    return sum(a * b for a, b in zip(left, right))


def _tokens(text: str) -> list[str]:
    base = [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
    expanded: list[str] = []
    for token in base:
        expanded.append(token)
        if "_" in token or "-" in token:
            expanded.extend(part for part in re.split(r"[_-]+", token) if part)
    return expanded


def _stable_index(value: str, dimensions: int) -> int:
    digest = hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dimensions


def _normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0.0:
        return vector
    return [value / magnitude for value in vector]


class SentenceTransformerEmbeddingProvider:
    """Embedding provider using local sentence-transformers models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as err:
            raise ImportError(
                "sentence-transformers is required to use SentenceTransformerEmbeddingProvider. "
                "Install it with `pip install semantic-tool-router[sentence-transformers]`"
            ) from err
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        embedding = self.model.encode(text, convert_to_numpy=True)
        # Ensure it returns list[float]
        return [float(x) for x in embedding.tolist()]


class OpenAIEmbeddingProvider:
    """Embedding provider using OpenAI's embedding API."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        try:
            import openai
        except ImportError as err:
            raise ImportError(
                "openai is required to use OpenAIEmbeddingProvider. "
                "Install it with `pip install semantic-tool-router[openai]`"
            ) from err
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            input=[text],
            model=self.model,
        )
        return [float(x) for x in response.data[0].embedding]


