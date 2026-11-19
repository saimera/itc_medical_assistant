import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.placidway.com/search-medical-pricings/Alternative-Medicine/All/1"
HTML_PATH = Path("data/raw/alternative-medicine-pricings.html")
OUTPUT_PATH = Path("data/processed/alternative_medicine_pricings.json")

# Download and save the raw page HTML.
response = requests.get(URL, timeout=30)
response.raise_for_status()

HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
HTML_PATH.write_text(response.text, encoding="utf-8")

# Parse the page and find its main content.
soup = BeautifulSoup(response.text, "html.parser")
main = soup.select_one(
    "main.article-dt-desc.ctm-dt-pages.search-pricing_page.pricing-new-design"
)

if main is None:
    raise ValueError("Main content container not found")

corpus = []

# Combine the page summary and Quick Facts into one overview record.
page_heading = soup.find("h1")
quick_facts = main.select_one(".pricing-facts-list")

if page_heading is None:
    raise ValueError("Page heading not found")

if quick_facts is None:
    raise ValueError("Quick Facts not found")

overview_parts = [page_heading.get_text(" ", strip=True)]

summary = page_heading.find_next("p")
if summary:
    overview_parts.append(summary.get_text(" ", strip=True))

facts = []
for row in quick_facts.select(".pricing-facts-row"):
    label = row.find("dt")
    value = row.find("dd")

    if label and value:
        facts.append(
            f"{label.get_text(' ', strip=True)}: "
            f"{value.get_text(' ', strip=True)}"
        )

overview_parts.extend(facts)

corpus.append({
    "id": "pricing-overview-001",
    "record_type": "pricing_overview",
    "title": page_heading.get_text(" ", strip=True),
    "text": "\n".join(overview_parts),
    "source_url": URL,
    "metadata": {"section_id": "quick-facts"},
})

# Store each of the two relevant price tables as one record.
tables = main.select("table")
if len(tables) < 2:
    raise ValueError("Expected pricing tables not found")

for table_number, table in enumerate(tables[:2], start=1):
    heading = table.find_previous("h2")
    title = (
        heading.get_text(" ", strip=True)
        if heading
        else f"Pricing Table {table_number}"
    )

    table_rows = []
    for row in table.select("tbody tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
        if any(cells):
            table_rows.append(cells)

    header = [cell.get_text(" ", strip=True) for cell in table.select("thead th")]
    markdown_rows = [
        f"| {' | '.join(header)} |",
        f"| {' | '.join(['---'] * len(header))} |",
    ]
    markdown_rows.extend(f"| {' | '.join(row)} |" for row in table_rows)

    corpus.append({
        "id": f"pricing-table-{table_number:03d}",
        "record_type": "pricing_table" if table_number == 1 else "cost_breakdown",
        "title": title,
        "text": "\n".join(markdown_rows),
        "source_url": URL,
        "metadata": {
            "section_id": (
                "price-ranges" if table_number == 1 else "cost-components"
            ),
            "scope": "general_alternative_medicine_estimates",
        },
    })

# Store typical inclusions and exclusions as separate records.
info_section = main.select_one(".info-sec")
if info_section is None:
    raise ValueError("Included and excluded information section not found")

for card in info_section.select(".info-card"):
    heading = card.find("h3")
    if heading is None:
        continue

    title = heading.get_text(" ", strip=True)
    description = card.select_one("p")
    items = [
        item.get_text(" ", strip=True)
        for item in card.select("ul li")
        if item.get_text(" ", strip=True)
    ]

    is_included = "good" in (card.get("class") or [])
    section_id = "typically-included" if is_included else "often-not-included"

    text_parts = []

    # Keep the description only for inclusions; it is misleading under exclusions.
    if is_included and description:
        text_parts.append(description.get_text(" ", strip=True))

    text_parts.extend(f"- {item}" for item in items)

    corpus.append({
        "id": f"{section_id}-001",
        "record_type": "package_inclusion" if is_included else "package_exclusion",
        "title": title,
        "text": "\n".join(text_parts),
        "source_url": URL,
        "metadata": {"section_id": section_id},
    })

# Store each FAQ question with its answer in one record.
faq_items = main.select(".faqs-list details")

for index, item in enumerate(faq_items, start=1):
    question_element = item.select_one("summary")
    answer_element = item.find("p")

    if question_element is None or answer_element is None:
        continue

    question = question_element.get_text(" ", strip=True)
    answer = answer_element.get_text(" ", strip=True)

    corpus.append({
        "id": f"faq-{index:03d}",
        "record_type": "faq",
        "title": question,
        "text": f"Question: {question}\nAnswer: {answer}",
        "source_url": URL,
        "metadata": {"section_id": "faqs"},
    })

# Save the page disclaimer about estimated pricing and health decisions.
disclaimer = soup.select_one("#disclaimer")
if disclaimer:
    disclaimer_text = disclaimer.get_text("\n", strip=True)

    corpus.append({
        "id": "disclaimer-001",
        "record_type": "disclaimer",
        "title": "Pricing and Health Disclaimer",
        "text": disclaimer_text,
        "source_url": URL,
        "metadata": {"section_id": "disclaimer"},
    })

# Write all extracted records to one corpus JSON file.
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(
    json.dumps(corpus, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"Saved {len(corpus)} records to {OUTPUT_PATH}")