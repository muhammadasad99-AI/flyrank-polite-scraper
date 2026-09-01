import os
import requests

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


if __name__ == "__main__":
    fetch_page("https://books.toscrape.com/catalogue/page-1.html", "catalogue-page-1.html")