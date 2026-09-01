import os
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime, timezone
import json
from pydantic import BaseModel, ValidationError, HttpUrl

CACHE_DIR = "cache"
HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/muhammadasad99-AI/flyrank-polite-scraper)"
}


def fetch_page(url: str, cache_filename: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch {url}: status {resp.status_code}")
    resp.encoding = "utf-8" 
    html = resp.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH: {cache_filename} ({len(html)} bytes)")
    time.sleep(0.5)  # be polite — only delay on real network requests
    return html


def get_book_links(html: str, page_url: str) -> list[str]:
    """Return absolute URLs to every book on this catalogue page."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for article in soup.find_all("article", class_="product_pod"):
        a_tag = article.find("h3").find("a")
        href = a_tag["href"]
        links.append(urljoin(page_url, href))
    return links


def get_next_page_url(html: str, page_url: str) -> str | None:
    """Return the absolute URL of the 'next' catalogue page, or None if there isn't one."""
    soup = BeautifulSoup(html, "html.parser")
    next_li = soup.find("li", class_="next")
    if next_li is None:
        return None
    href = next_li.find("a")["href"]
    return urljoin(page_url, href)

def extract_book(html: str, product_url: str, source_page: str) -> dict:
    """Extract one raw book record from a book detail page."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1").get_text(strip=True)

    price_text = soup.find("p", class_="price_color").get_text(strip=True)

    availability_text = soup.find("p", class_="instock availability").get_text(strip=True)
    availability_text = " ".join(availability_text.split())  # collapse extra whitespace/newlines

    rating_tag = soup.find("p", class_=re.compile(r"star-rating"))
    rating_classes = rating_tag["class"]  # e.g. ["star-rating", "Three"]
    rating_text = [c for c in rating_classes if c != "star-rating"][0]

    desc_div = soup.find("div", id="product_description")
    if desc_div is not None:
        description = desc_div.find_next_sibling("p").get_text(strip=True)
    else:
        description = None

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def cache_name_for_book(url: str) -> str:
    """Turn a book URL into a safe cache filename, e.g. a-light-in-the-attic_1000.html"""
    slug = url.rstrip("/").split("/")[-2]  # the folder name before index.html
    return f"book-{slug}.html"

class Book(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: str | None
    source_page: str
    fetched_at: str
    
    
def clean_record(raw: dict) -> dict:
    """Add a numeric price_gbp field to a raw record."""
    price_text = raw["price_text"]
    numeric = "".join(ch for ch in price_text if ch.isdigit() or ch == ".")
    price_gbp = float(numeric)

    cleaned = dict(raw)
    cleaned["price_gbp"] = price_gbp
    return cleaned


    
if __name__ == "__main__":
    MAX_PAGES = 3
    start_url = "https://books.toscrape.com/catalogue/page-1.html"
    current_url = start_url
    page_num = 1
    book_links_with_source = []  # list of (book_url, source_page)

    while current_url is not None and page_num <= MAX_PAGES:
        cache_name = f"catalogue-page-{page_num}.html"
        html = fetch_page(current_url, cache_name)

        page_links = get_book_links(html, current_url)
        for link in page_links:
            book_links_with_source.append((link, current_url))

        current_url = get_next_page_url(html, current_url)
        page_num += 1

    # dedupe by URL, keep first source_page seen
    seen = {}
    for url, source in book_links_with_source:
        if url not in seen:
            seen[url] = source
    unique_books = list(seen.items())

    print(f"catalogue_pages={min(page_num - 1, MAX_PAGES)}")
    print(f"discovered={len(book_links_with_source)}")
    print(f"unique_urls={len(unique_books)}")

    # Stage 3: extract every book
    records = []
    for product_url, source_page in unique_books:
        cache_name = cache_name_for_book(product_url)
        book_html = fetch_page(product_url, cache_name)
        record = extract_book(book_html, product_url, source_page)
        records.append(record)

    print(f"detail_pages={len(records)}")
    print("\nSample record:")
    print(records[0])
    
    valid_books = []
    errors = []
    seen_urls = set()

    for raw in records:
        cleaned = clean_record(raw)
        try:
            book = Book(**cleaned)
            if book.product_url not in seen_urls:
                seen_urls.add(book.product_url)
                valid_books.append(book.model_dump())
        except ValidationError as e:
            errors.append({"record": cleaned, "reason": str(e)})

    os.makedirs("output", exist_ok=True)
    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(valid_books, f, indent=2, ensure_ascii=False)

    with open("output/errors.json", "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2, ensure_ascii=False)

    print(f"valid_records={len(valid_books)}")
    print(f"invalid_records={len(errors)}")