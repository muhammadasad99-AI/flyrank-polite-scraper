import os
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

CACHE_DIR = "cache"
HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/muhammadasad99-AI/flyrank-polite-scraper)"
}


def fetch_page(url: str, cache_filename: str) -> str:
    """Fetch a page, using a local cache if available. Returns the HTML as a string."""
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

    html = resp.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH: {cache_filename} ({len(html)} bytes)")
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


if __name__ == "__main__":
    MAX_PAGES = 3
    start_url = "https://books.toscrape.com/catalogue/page-1.html"
    current_url = start_url
    page_num = 1
    all_links = []

    while current_url is not None and page_num <= MAX_PAGES:
        cache_name = f"catalogue-page-{page_num}.html"
        html = fetch_page(current_url, cache_name)

        page_links = get_book_links(html, current_url)
        all_links.extend(page_links)

        current_url = get_next_page_url(html, current_url)
        page_num += 1

    unique_links = list(dict.fromkeys(all_links))  # dedupe, preserve order

    print(f"catalogue_pages={min(page_num - 1, MAX_PAGES)}")
    print(f"discovered={len(all_links)}")
    print(f"unique_urls={len(unique_links)}")