from pathlib import Path
import json

input_path = Path("data/processed/itc-corpus.json")
output_path = Path("data/processed/itc-profile.md")

records = json.loads(input_path.read_text(encoding="utf-8"))
markdown_parts = []

# Normalize record text so markdown labels are not duplicated in the rendered content.
for record in records:
    title = record["title"].strip()
    text = record["text"].strip()
    record_type = record["record_type"]

    question_prefix = f"Question: {title}"
    if text.startswith(question_prefix):
        text = text[len(question_prefix):].lstrip()
    elif text.startswith(title):
        text = text[len(title):].lstrip()

    markdown_parts.append(
        f"## {title}\n\n**Type:** {record_type}\n\n{text}"
    )

# Write a single markdown document with clear dividers between source records.
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(
    "\n\n---\n\n".join(markdown_parts),
    encoding="utf-8",
)

print(f"Created {len(records)} Markdown sections: {output_path}")