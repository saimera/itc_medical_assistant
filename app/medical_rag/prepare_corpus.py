import json
from pathlib import Path


# Load the processed source files that will be merged into one corpus.
data_dir = Path("data/processed")


def load_records(filename):
    path = data_dir / filename
    return json.loads(path.read_text(encoding="utf-8"))


documents = []

for index, record in enumerate(load_records("itc-profile-sections.json"), start=1):
    documents.append({
        "id": f"profile-{index:03d}",
        "record_type": "profile_section",
        "title": record["section"],
        "text": record["text"],
        "source_url": record["source_url"],
        "metadata": {"section_id": record["section_id"]},
    })

for index, record in enumerate(load_records("itc-faqs.json"), start=1):
    documents.append({
        "id": f"faq-{index:03d}",
        "record_type": "faq",
        "title": record["question"],
        "text": f"Question: {record['question']}\nAnswer: {record['answer']}",
        "source_url": record["source_url"],
        "metadata": {"section_id": record["section_id"]},
    })

for index, record in enumerate(load_records("itc-reviews.json"), start=1):
    documents.append({
        "id": f"review-{index:03d}",
        "record_type": "review",
        "title": f"Review by {record['reviewer'] or 'Guest'}",
        "text": record["text"],
        "source_url": record["source_url"],
        "metadata": {
            "reviewer": record["reviewer"],
            "date": record["date"],
            "rating": record["rating"],
            "context": record["context"],
        },
    })

for index, record in enumerate(load_records("itc-testimonials.json"), start=1):
    documents.append({
        "id": f"testimonial-{index:03d}",
        "record_type": "testimonial",
        "title": record["title"],
        "text": record["text"],
        "source_url": record["source_url"],
        "metadata": {"section_id": record["section_id"]},
    })

# Write the merged corpus so downstream ingestion can work from one file.
output_path = data_dir / "itc-corpus.json"
output_path.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved {len(documents)} records to {output_path}")

