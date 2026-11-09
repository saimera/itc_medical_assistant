from pathlib import Path  # File paths aur folders handle karne ke liye
import json  # JSON files banane ke liye

import requests  # Web page download karne ke liye
from bs4 import BeautifulSoup, Comment  # HTML parse karne aur comments remove karne ke liye

url = "https://www.placidway.com/profile/5/Alternative-Cancer-Treatment-by-ITC-Immunity-Therapy-Center"  # Scrape ki jane wali page URL

response = requests.get(url, timeout=30)  # Page download karo; 30 seconds baad timeout ho
response.raise_for_status()  # HTTP error aaye to execution rok do

Path("data/raw/itc-profile.html").write_text(response.text, encoding="utf-8")  # Original HTML save karo

soup = BeautifulSoup(response.text, "html.parser")  # HTML parse karo

for comment in soup.find_all(string=lambda item: isinstance(item, Comment)):  # HTML comments dhoondo
    comment.extract()  # Comments jaise "CTA 1" labels hatao

for popup_id in [  # Remove karne wale popup IDs
    "request_video_call_popup",  # Video-call popup
    "book_consultation_popup",  # Booking popup
    "confirm_vs_popup",  # Consultation confirmation popup
]:
    popup = soup.find(id=popup_id)  # Popup dhoondo
    if popup:  # Popup milne par
        popup.decompose()  # HTML se popup hatao

for tag in soup(["script", "style", "noscript", "nav", "header", "footer"]):  # Non-content aur common site sections dhoondo
    tag.decompose()  # HTML se un sections ko hatao

main = soup.select_one("main.article-dt-desc")  # Profile content container dhoondo

testimonial_section = main.find("section", id="testimonials")  # Testimonials section dhoondo
testimonial_records = []  # Written story records rakhne ki list

if testimonial_section:  # Section milne par
    for heading in testimonial_section.select("h4"):  # Patient-story headings par jao
        title = " ".join(heading.get_text(" ", strip=True).split())  # Story title saaf karo
        block = heading.parent  # Story ka content block lo
        block_text = " ".join(block.get_text(" ", strip=True).split())  # Block text saaf karo
        body = block_text[len(title):].strip() if block_text.startswith(title) else block_text  # Title ke baad story text lo

        if body:  # Written story maujood ho to
            testimonial_records.append({  # Story ka record banao
                "title": title,  # Story title save karo
                "text": body,  # Story text save karo
                "section_id": "testimonials",  # Section ID save karo
                "source_url": url,  # Source URL save karo
            })

testimonial_path = Path("data/processed/itc-testimonials.json")  # Testimonials JSON path
testimonial_path.parent.mkdir(parents=True, exist_ok=True)  # Output folder banao
testimonial_path.write_text(json.dumps(testimonial_records, ensure_ascii=False, indent=2), encoding="utf-8")  # Stories save karo
print(f"Saved {len(testimonial_records)} written testimonials to {testimonial_path}")  # Saved count dikhao


if main is None:  # Container na mile to
    raise ValueError("Profile content container not found")  # Saaf error dikhao

review_section = main.find("section", id="reviews")  # Reviews section dhoondo
review_records = []  # Review records rakhne ki list

if review_section:  # Reviews section milne par
    for card in review_section.select(".review-card"):  # Har review card par jao
        body = card.select_one(".review-body")  # Review text dhoondo
        rating = card.select_one(".star-rating")  # Rating dhoondo
        reviewer = card.select_one(".reviewer-name")  # Reviewer ka naam dhoondo
        review_date = card.select_one(".review-date")  # Review ki date dhoondo
        context = card.select_one("small")  # Review ka associated label dhoondo

        review_records.append({  # Review ka record banao
            "reviewer": reviewer.get_text(" ", strip=True) if reviewer else None,  # Naam save karo
            "date": review_date.get_text(" ", strip=True) if review_date else None,  # Date save karo
            "rating": rating.get("data-rating") if rating else None,  # Rating save karo
            "context": context.get_text(" ", strip=True) if context and context.get_text(strip=True) else None,  # Label ho to save karo
            "text": body.get_text(" ", strip=True) if body else "",  # Review text save karo
            "source_url": url,  # Source URL save karo
        })

review_path = Path("data/processed/itc-reviews.json")  # Reviews JSON file ka path
review_path.parent.mkdir(parents=True, exist_ok=True)  # Output folder banao, agar zaroori ho
review_path.write_text(json.dumps(review_records, ensure_ascii=False, indent=2), encoding="utf-8")  # Reviews save karo
print(f"Saved {len(review_records)} review records to {review_path}")  # Saved review count dikhao

faq_text = main.find(  # FAQ heading ka text dhoondo
    string=lambda text: text and text.strip() == "Frequently Asked Questions"
)
faq_h2 = faq_text.parent if faq_text else None  # FAQ heading ka h2 element lo
faq_records = []  # FAQ records rakhne ki list

if faq_h2:  # FAQ section milne par
    for question in faq_h2.find_all_next("h3"):  # FAQ ke question headings par jao
        if question.find_previous("h2") is not faq_h2:  # Agla main section shuru ho to
            break  # FAQ questions se aage na jao

        answer = question.find_next_sibling("p")  # Sawal ke baad wala jawab dhoondo
        if answer:  # Jawab maujood ho to
            faq_records.append({  # Sawal-jawab ka record banao
                "question": question.get_text(" ", strip=True),  # Sawal save karo
                "answer": answer.get_text(" ", strip=True),  # Jawab save karo
                "section_id": "about",  # Parent section ID save karo
                "source_url": url,  # Source URL save karo
            })

faq_path = Path("data/processed/itc-faqs.json")  # FAQ JSON file ka path
faq_path.parent.mkdir(parents=True, exist_ok=True)  # Output folder banao, agar zaroori ho
faq_path.write_text(json.dumps(faq_records, ensure_ascii=False, indent=2), encoding="utf-8")  # FAQs save karo
print(f"Saved {len(faq_records)} FAQ records to {faq_path}")  # Saved FAQ count dikhao

records = []  # Profile content records rakhne ki list
about_section = main.find("section", id="about")  # Overview section dhoondo

if about_section:  # Overview section milne par
    first_heading = about_section.find("h2")  # Outer Profile Overview heading lo

    for heading in about_section.select("h2"):  # Inner subsection headings par jao
        title = heading.get_text(" ", strip=True)  # Heading text nikalo
        if heading is first_heading or title in {  # Outer heading aur alag files mein saved content skip karo
            "Frequently Asked Questions",
            "Get More Information About Treatment Eligibility",
        }:
            continue  # Is heading ka record na banao

        block = heading.parent  # Is subsection ka HTML block lo
        text = " ".join(block.get_text(" ", strip=True).split())  # Text aur whitespace saaf karo

        records.append({  # Subsection ka record banao
            "section_id": "about",  # Parent section ID save karo
            "section": title,  # Subsection heading save karo
            "text": text,  # Subsection text save karo
            "source_url": url,  # Source URL save karo
        })

for section in main.select("section.js-toc-section"):  # Baaki profile sections par jao
    section_id = section.get("id")  # HTML section ID lo
    if section_id in {"about", "reviews", "testimonials"}:  # Alag process kiye gaye sections skip karo
        continue  # Duplicate broad record na banao

    heading = section.find(["h2", "h3"])  # Section heading dhoondo
    text = " ".join(section.get_text(" ", strip=True).split())  # Section text aur whitespace saaf karo

    records.append({  # Section ka record banao
        "section_id": section_id,  # HTML section ID save karo
        "section": heading.get_text(" ", strip=True) if heading else "Untitled section",  # Heading save karo
        "text": text,  # Section text save karo
        "source_url": url,  # Source URL save karo
    })

output_path = Path("data/processed/itc-profile-sections.json")  # Profile JSON file ka path
output_path.parent.mkdir(parents=True, exist_ok=True)  # Output folder banao, agar zaroori ho
output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")  # Sections save karo
print(f"Saved {len(records)} sections to {output_path}")  # Saved record count dikhao

text = soup.get_text(separator="\n", strip=True)  # Cleaned page ka readable text nikalo
Path("data/raw/itc-profile.txt").write_text(text, encoding="utf-8")  # Readable text file save karo
print(f"Extracted {len(text)} characters to data/raw/itc-profile.txt")  # Extracted text count dikhao