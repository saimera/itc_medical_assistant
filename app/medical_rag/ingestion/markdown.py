from pathlib import Path  # File paths handle karne ke liye
import json  # JSON corpus read karne ke liye

input_path = Path("data/processed/itc-corpus.json")  # Corpus JSON ka path
output_path = Path("data/processed/itc-profile.md")  # Markdown output ka path

records = json.loads(input_path.read_text(encoding="utf-8"))  # JSON records load karo
markdown_parts = []  # Markdown sections jama karne ke liye

for record in records:  # Har corpus record par jao
    title = record["title"].strip()  # Record ka title lo
    text = record["text"].strip()  # Record ka text lo
    record_type = record["record_type"]  # Record ka type lo

    question_prefix = f"Question: {title}"  # FAQ mein duplicate sawal pehchano
    if text.startswith(question_prefix):  # FAQ text sawal se shuru ho to
        text = text[len(question_prefix):].lstrip()  # Duplicate sawal hatao
    elif text.startswith(title):  # Text title se shuru ho to
        text = text[len(title):].lstrip()  # Duplicate title hatao

    markdown_parts.append(  # Record ko Markdown section mein badlo
        f"## {title}\n\n**Type:** {record_type}\n\n{text}"
    )

output_path.parent.mkdir(parents=True, exist_ok=True)  # Output folder zaroorat par banao
output_path.write_text(  # Markdown file save karo
    "\n\n---\n\n".join(markdown_parts),  # Records ke darmiyan separator rakho
    encoding="utf-8",
)

print(f"Created {len(records)} Markdown sections: {output_path}")  # Result dikhao