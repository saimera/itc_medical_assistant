import os

import requests

JINA_API_URL = "https://api.jina.ai/v1/embeddings"
JINA_MODEL = "jina-embeddings-v5-text-small"
EMBEDDING_DIMENSION = 1024


def embed_text(texts: list[str]) -> list[list[float]]:
    api_key = os.getenv("JINA_API_KEY")

    if not api_key:
        raise ValueError("JINA_API_KEY is missing from .env")

    response = requests.post(
        JINA_API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": JINA_MODEL,
            "task": "retrieval.passage",
            "dimensions": EMBEDDING_DIMENSION,
            "input": texts,
        },
        timeout=60,
    )
    response.raise_for_status()

    results = sorted(response.json()["data"], key=lambda item: item["index"])
    embeddings = [item["embedding"] for item in results]

    if len(embeddings) != len(texts):
        raise RuntimeError("Jina returned a different number of embeddings than inputs")

    return embeddings