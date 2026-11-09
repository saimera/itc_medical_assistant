import json  # JSON files read aur write karne ke liye
from pathlib import Path  # File paths handle karne ke liye


data_dir = Path("data/processed")  # Processed JSON files ka folder

def load_records(filename):  # JSON file se records load karne ka function
    path = data_dir / filename  # File ka path banao
    return json.loads(path.read_text(encoding="utf-8"))  # File ka JSON Python data mein badlo

documents = []  # Normalized records rakhne ki list

for index, record in enumerate(load_records("itc-profile-sections.json"), start=1):  # Profile sections par jao
    documents.append({  # Common-format document banao
        "id": f"profile-{index:03d}",  # Unique record ID do
        "record_type": "profile_section",  # Record ka type set karo
        "title": record["section"],  # Section heading title banao
        "text": record["text"],  # Section content rakho
        "source_url": record["source_url"],  # Source URL rakho
        "metadata": {"section_id": record["section_id"]},  # Section ID metadata mein rakho
    })

for index, record in enumerate(load_records("itc-faqs.json"), start=1):  # FAQs par jao
    documents.append({  # Common-format FAQ document banao
        "id": f"faq-{index:03d}",  # Unique record ID do
        "record_type": "faq",  # Record ka type set karo
        "title": record["question"],  # Sawal ko title banao
        "text": f"Question: {record['question']}\nAnswer: {record['answer']}",  # Sawal aur jawab jodo
        "source_url": record["source_url"],  # Source URL rakho
        "metadata": {"section_id": record["section_id"]},  # Section ID metadata mein rakho
    })

for index, record in enumerate(load_records("itc-reviews.json"), start=1):  # Reviews par jao
    documents.append({  # Common-format review document banao
        "id": f"review-{index:03d}",  # Unique record ID do
        "record_type": "review",  # Record ka type set karo
        "title": f"Review by {record['reviewer'] or 'Guest'}",  # Reviewer se title banao
        "text": record["text"],  # Review content rakho
        "source_url": record["source_url"],  # Source URL rakho
        "metadata": {  # Review details metadata mein rakho
            "reviewer": record["reviewer"],
            "date": record["date"],
            "rating": record["rating"],
            "context": record["context"],
        },
    })

for index, record in enumerate(load_records("itc-testimonials.json"), start=1):  # Written testimonials par jao
    documents.append({  # Common-format testimonial document banao
        "id": f"testimonial-{index:03d}",  # Unique record ID do
        "record_type": "testimonial",  # Record ka type set karo
        "title": record["title"],  # Story title rakho
        "text": record["text"],  # Story content rakho
        "source_url": record["source_url"],  # Source URL rakho
        "metadata": {"section_id": record["section_id"]},  # Section ID metadata mein rakho
    })

output_path = data_dir / "itc-corpus.json"  # Combined corpus file ka path
output_path.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")  # Corpus JSON save karo
print(f"Saved {len(documents)} records to {output_path}")  # Saved records ki tadaad dikhao


