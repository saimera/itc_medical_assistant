import json
from pathlib import Path

from bs4 import BeautifulSoup


# Load the saved HTML and parse it.
HTML_PATH = Path("data/raw/itc-price-list.html")
OUTPUT_PATH = Path("data/processed/itc_price_list.json")
SOURCE_URL = "https://www.placidway.com/price-list/5/Alternative-Cancer-Treatment-by-ITC-Immunity-Therapy-Center"

html = HTML_PATH.read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")

# Find the main content container.
main = soup.select_one("main.article-dt-desc.ctm-dt-pages")
if main is None:
    raise ValueError("Main content container not found")

corpus = []

# Collect all valid pricing rows for one pricing-table record.
table = main.select_one("section#prices table")
if table is None:
    raise ValueError("Pricing table not found")

price_rows = []

for row in table.select("tbody tr"):
    cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]

    # Skip rows without a procedure name or price.
    if len(cells) < 3 or not cells[0] or not cells[2]:
        continue

    procedure, details, price = cells[:3]
    price_rows.append(f"| {procedure} | {details} | {price} |")

if price_rows:
    pricing_text = "\n".join([
        "| Procedure | Details | Price (USD) |",
        "|---|---|---|",
        *price_rows,
    ])

    corpus.append({
        "id": "price-table-001",
        "record_type": "pricing_table",
        "title": "ITC Immunity Therapy Center Cancer Treatment Prices",
        "text": pricing_text,
        "source_url": SOURCE_URL,
        "metadata": {"section_id": "prices"},
    })

# Extract the About section and keep its paragraphs separate.
about = main.select_one("section#about")
if about is None:
    raise ValueError("About section not found")

about_heading = about.find(["h2", "h3"])
about_title = (
    about_heading.get_text(" ", strip=True)
    if about_heading
    else "About ITC Immunity Therapy Center"
)

about_paragraphs = [
    paragraph.get_text(" ", strip=True)
    for paragraph in about.select("p")
    if paragraph.get_text(" ", strip=True)
]

if about_paragraphs:
    corpus.append({
        "id": "about-001",
        "record_type": "profile_section",
        "title": about_title,
        "text": "\n\n".join(about_paragraphs),
        "source_url": SOURCE_URL,
        "metadata": {"section_id": "about"},
    })


# --- enabled only when some new review data is available as current reveiws are duplicates, they are already in the db  ---

# Extract each review with its reviewer, date, and rating metadata.
# review_cards = main.select(".review-container .review-card")

# for index, card in enumerate(review_cards, start=1):
#     reviewer_element = card.select_one(".reviewer-name")
#     date_element = card.select_one(".review-date")
#     rating_element = card.select_one(".star-rating")
#     text_element = card.select_one(".review-body")

#     review_text = text_element.get_text(" ", strip=True) if text_element else ""
#     if not review_text:
#         continue

#     reviewer = (
#         reviewer_element.get_text(" ", strip=True)
#         if reviewer_element
#         else "Guest"
#     )
#     date = date_element.get_text(" ", strip=True) if date_element else None
#     rating = rating_element.get("data-rating") if rating_element else None

#     corpus.append({
#         "id": f"review-{index:03d}",
#         "record_type": "review",
#         "title": f"Review by {reviewer}",
#         "text": review_text,
#         "source_url": SOURCE_URL,
#         "metadata": {
#             "section_id": "reviews",
#             "reviewer": reviewer,
#             "date": date,
#             "rating": rating,
#         },
#     })

# Save all records into one corpus JSON file.
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(
    json.dumps(corpus, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"Saved {len(corpus)} records to {OUTPUT_PATH}")