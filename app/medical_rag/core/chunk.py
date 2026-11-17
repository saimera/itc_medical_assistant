import re

from tokenizers import Tokenizer

TOKENIZER = Tokenizer.from_pretrained("nvidia/llama-nemotron-embed-1b-v2")
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


def split_markdown(markdown: str) -> list[str]:
    records = re.split(r"(?m)^---\s*$", markdown)
    chunks = []

    for record in records:
        record = record.strip()
        if not record:
            continue

        parts = record.split("\n\n", 2)
        tokens = TOKENIZER.encode(record, add_special_tokens=False).ids

        if len(tokens) <= CHUNK_SIZE or len(parts) < 3:
            chunks.append(record)
            continue

        context = "\n\n".join(parts[:2])
        body = parts[2].strip()
        prefix = f"{context}\n\n"
        prefix_tokens = len(
            TOKENIZER.encode(prefix, add_special_tokens=False).ids
        )
        body_size = CHUNK_SIZE - prefix_tokens - 5
        step = body_size - CHUNK_OVERLAP

        if step <= 0:
            raise ValueError(f"Title/type too long for chunk size: {context}")

        body_tokens = TOKENIZER.encode(body, add_special_tokens=False).ids

        for start in range(0, len(body_tokens), step):
            piece_tokens = body_tokens[start : start + body_size]
            piece = TOKENIZER.decode(piece_tokens).strip()
            chunks.append(f"{prefix}{piece}".strip())

    return chunks