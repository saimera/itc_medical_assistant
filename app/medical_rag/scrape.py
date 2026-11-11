import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Comment

URL = "https://www.placidway.com/profile/5/Alternative-Cancer-Treatment-by-ITC-Immunity-Therapy-Center"

response = requests.get(URL, timeout=30)
response.raise_for_status()

Path("data/raw/itc-profile.html").write_text(response.text, encoding="utf-8")

soup = BeautifulSoup(response.text, "html.parser")

# Remove HTML comments and non-content blocks that would pollute the scraped data.
for comment in soup.find_all(string=lambda item: isinstance(item, Comment)):
    comment.extract()

for popup_id in [
    "request_video_call_popup",
    "book_consultation_popup",
    "confirm_vs_popup",
]:
    popup = soup.find(id=popup_id)
    if popup:
        popup.decompose()

for tag in soup(["script", "style", "noscript", "nav", "header", "footer"]):
    tag.decompose()

main = soup.select_one("main.article-dt-desc")

# Extract written testimonial stories.
testimonial_section = main.find("section", id="testimonials")
testimonial_records = []

if testimonial_section:
    for heading in testimonial_section.select("h4"):
        title = " ".join(heading.get_text(" ", strip=True).split())
        block = heading.parent
        block_text = " ".join(block.get_text(" ", strip=True).split())
        body = block_text[len(title):].strip() if block_text.startswith(title) else block_text

        if body:
            testimonial_records.append({
                "title": title,
                "text": body,
                "section_id": "testimonials",
                "source_url": URL,
            })

testimonial_path = Path("data/processed/itc-testimonials.json")
testimonial_path.parent.mkdir(parents=True, exist_ok=True)
testimonial_path.write_text(json.dumps(testimonial_records, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved {len(testimonial_records)} written testimonials to {testimonial_path}")

if main is None:
    raise ValueError("Profile content container not found")

# Extract review details from the review cards.
review_section = main.find("section", id="reviews")
review_records = []

if review_section:
    for card in review_section.select(".review-card"):
        body = card.select_one(".review-body")
        rating = card.select_one(".star-rating")
        reviewer = card.select_one(".reviewer-name")
        review_date = card.select_one(".review-date")
        context = card.select_one("small")

        review_records.append({
            "reviewer": reviewer.get_text(" ", strip=True) if reviewer else None,
            "date": review_date.get_text(" ", strip=True) if review_date else None,
            "rating": rating.get("data-rating") if rating else None,
            "context": context.get_text(" ", strip=True) if context and context.get_text(strip=True) else None,
            "text": body.get_text(" ", strip=True) if body else "",
            "source_url": URL,
        })

review_path = Path("data/processed/itc-reviews.json")
review_path.parent.mkdir(parents=True, exist_ok=True)
review_path.write_text(json.dumps(review_records, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved {len(review_records)} review records to {review_path}")

# Extract FAQ pairs from the page's FAQ section.
faq_text = main.find(
    string=lambda text: text and text.strip() == "Frequently Asked Questions"
)
faq_h2 = faq_text.parent if faq_text else None
faq_records = []

if faq_h2:
    for question in faq_h2.find_all_next("h3"):
        if question.find_previous("h2") is not faq_h2:
            break

        answer = question.find_next_sibling("p")
        if answer:
            faq_records.append({
                "question": question.get_text(" ", strip=True),
                "answer": answer.get_text(" ", strip=True),
                "section_id": "about",
                "source_url": URL,
            })

faq_path = Path("data/processed/itc-faqs.json")
faq_path.parent.mkdir(parents=True, exist_ok=True)
faq_path.write_text(json.dumps(faq_records, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved {len(faq_records)} FAQ records to {faq_path}")

# Capture the main profile sections for further normalization.
records = []
about_section = main.find("section", id="about")

if about_section:
    first_heading = about_section.find("h2")

    for heading in about_section.select("h2"):
        title = heading.get_text(" ", strip=True)
        if heading is first_heading or title in {
            "Frequently Asked Questions",
            "Get More Information About Treatment Eligibility",
        }:
            continue

        block = heading.parent
        text = " ".join(block.get_text(" ", strip=True).split())

        records.append({
            "section_id": "about",
            "section": title,
            "text": text,
            "source_url": URL,
        })

for section in main.select("section.js-toc-section"):
    section_id = section.get("id")
    if section_id in {"about", "reviews", "testimonials"}:
        continue

    heading = section.find(["h2", "h3"])
    text = " ".join(section.get_text(" ", strip=True).split())

    records.append({
        "section_id": section_id,
        "section": heading.get_text(" ", strip=True) if heading else "Untitled section",
        "text": text,
        "source_url": URL,
    })

# Save the normalized section dataset and a plain-text fallback.
output_path = Path("data/processed/itc-profile-sections.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved {len(records)} sections to {output_path}")

text = soup.get_text(separator="\n", strip=True)
Path("data/raw/itc-profile.txt").write_text(text, encoding="utf-8")
print(f"Extracted {len(text)} characters to data/raw/itc-profile.txt")