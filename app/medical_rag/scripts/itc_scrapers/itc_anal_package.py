import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.placidway.com/package/7901/Alternative-Anal-Cancer-Treatment-Package-in-Tijuana-Mexico-by-ITC"
HTML_PATH = Path("data/raw/itc-anal-package.html")
OUTPUT_PATH = Path("data/processed/itc-anal-package-corpus.json")

response = requests.get(URL, timeout=30)
response.raise_for_status()

HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
HTML_PATH.write_text(response.text, encoding="utf-8")

soup = BeautifulSoup(response.text, "html.parser")
package_content = soup.select_one("section#about.speakable-text")

if package_content is None:
    raise ValueError("Package content section not found")

corpus = []

highlight_heading = next(
    (
        heading
        for heading in package_content.select("h2")
        if "Start Your Personalized Healing Journey"
        in heading.get_text(" ", strip=True)
    ),
    None,
)

if highlight_heading is None:
    raise ValueError("Package highlights section not found")

# Keep each highlight as a separate Markdown bullet.
highlight_text = [
    f"- {item.get_text(' ', strip=True)}"
    for item in highlight_heading.parent.select("ul > li")
]

corpus.append({
    "id": "package-section-001",
    "record_type": "package_section",
    "title": highlight_heading.get_text(" ", strip=True),
    "text": "\n".join(highlight_text),
    "source_url": URL,
    "metadata": {"section_id": "about"},
})

section_number = 1

for heading in package_content.select("h2"):
    title = heading.get_text(" ", strip=True)

    if title.startswith(("FAQs:", "Start Your Personalized Healing Journey")):
        continue

    section_text = []

    for item in heading.next_siblings:
        if getattr(item, "name", None) == "h2":
            break

        # Preserve each list item as its own Markdown bullet.
        if getattr(item, "name", None) in {"ul", "ol"}:
            section_text.extend(
                f"- {li.get_text(' ', strip=True)}"
                for li in item.find_all("li", recursive=False)
            )
            continue

        text = (
            item.get_text(" ", strip=True)
            if hasattr(item, "get_text")
            else str(item).strip()
        )
        if text:
            section_text.append(text)

    section_number += 1
    corpus.append({
        "id": f"package-section-{section_number:03d}",
        "record_type": "package_section",
        "title": title,
        # Keep paragraphs and bullets separated in the saved corpus.
        "text": "\n".join(section_text),
        "source_url": URL,
        "metadata": {"section_id": "about"},
    })

faq_heading = next(
    (
        heading
        for heading in package_content.select("h2")
        if heading.get_text(" ", strip=True).startswith("FAQs:")
    ),
    None,
)

if faq_heading is None:
    raise ValueError("FAQ section not found")

faq_number = 0

for question in faq_heading.find_all_next("h3"):
    if question.find_previous("h2") is not faq_heading:
        break

    answer = question.find_next_sibling("p")
    if answer is None:
        continue

    faq_number += 1
    question_text = question.get_text(" ", strip=True)

    corpus.append({
        "id": f"package-faq-{faq_number:03d}",
        "record_type": "faq",
        "title": question_text,
        "text": (
            f"Question: {question_text}\n"
            f"Answer: {answer.get_text(' ', strip=True)}"
        ),
        "source_url": URL,
        "metadata": {"section_id": "about"},
    })

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(
    json.dumps(corpus, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"Saved {len(corpus)} records to {OUTPUT_PATH}")