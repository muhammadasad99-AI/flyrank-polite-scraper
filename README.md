# The Polite Scraper

A small, polite scraping pipeline for [Books to Scrape](https://books.toscrape.com) — a public sandbox site built for practicing web scraping. This project fetches the first 3 catalogue pages, discovers all 60 linked books, extracts and validates a clean record for each, and survives broken pages without crashing.

Built for FlyRank Internship, Backend Track, Week 5, Assignment A9.

## Target classification

- **Site:** https://books.toscrape.com
- **Why:** A public sandbox site built specifically for people to practice web scraping on (confirmed at toscrape.com).
- **Scope:** The first 3 catalogue pages, and the 60 book detail pages linked from them — nothing else.
- **Data collected:** Book title, price, availability, star rating, description, and page URL.
- **robots.txt result:** Requested `https://books.toscrape.com/robots.txt` — returned a 404 Not Found. No robots file found.
- I will not reuse this code on another site without checking its rules and terms first.

## Lane & install

Python 3.10+, using `requests`, `beautifulsoup4`, and `pydantic`.

```powershell
pip install requests beautifulsoup4 pydantic
```

## How to run

```powershell
python src\main.py
```

This will:
1. Fetch (or read from cache) the first 3 catalogue pages
2. Discover all 60 unique book URLs
3. Fetch (or read from cache) each of the 60 book detail pages
4. Extract, clean, and validate a record for each book
5. Write `output/books.json`, `output/errors.json`, and `output/run-report.json`

Running it a second time reads everything from `cache/` instead of hitting the site again, and still produces exactly 60 records (idempotent).

## Politeness rules followed

- **User-agent:** every request identifies itself as `FlyRankInternshipA9/1.0 (+<repo-url>)`
- **Timeout:** every request gives up after 15 seconds
- **Delay:** at least 0.5 seconds between real (non-cached) requests
- **Caching:** every fetched page is saved to `cache/` and reused on subsequent runs — the site is only hit once per unique page
- **Status check:** only a `200` response is treated as a successful fetch
- **Retry policy:** timeouts and 5xx server errors are retried once; 404 and 403 are never retried

## Record schema (validated, Stage 4)

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-09-01T17:26:58.994480+00:00"
}
```

`description` is `null` when a book page has no description section — nothing is invented. Records are validated with Pydantic before storage; anything that fails validation goes to `output/errors.json` with a reason instead of `books.json`.

## Sample run report

To prove the failure-handling works, one deliberately fake book URL was added to a test run. The scraper logged it, skipped it, and finished normally with the other 60 records intact:

```json
{
  "start_time": "2026-09-01T17:48:53.197994+00:00",
  "duration_seconds": 230.217317,
  "pages_fetched": 61,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1,
  "failures": [
    {
      "url": "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html",
      "reason": "Failed to fetch https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html: status 404 (not retrying)"
    }
  ]
}
```

## Why no browser was needed

The book data (title, price, availability, description) is present directly in the server-rendered HTML — there is no JavaScript-rendered content to wait for, so a browser like Playwright would only add cost (memory, startup time) with no benefit here.

## Ethics note

This scraper only touches a sandbox site explicitly built for scraping practice. In real projects: check for and prefer an official API before scraping; never bypass logins, paywalls, or access blocks; only collect the data actually needed for the task; and always identify the scraper honestly via user-agent so a site owner can see who is visiting and why.

## Known limitation

Response encoding is forced to UTF-8 on fetch to avoid mangled special characters (e.g. `£` appearing as `Â£`). The scraper does not yet handle pagination changes on the live site gracefully beyond the first 3 pages — it is deliberately scoped to that limit per the assignment.

## Progress

- [x] Stage 0 — Target classification
- [x] Stage 1 — Fetch once, cache once
- [x] Stage 2 — Discover three catalogue pages (60 unique URLs)
- [x] Stage 3 — Extract raw records from all 60 book pages
- [x] Stage 4 — Clean, validate, and store as `books.json`
- [x] Stage 5 — Survive failures and write a run report
- [x] Stage 6 — Publish evidence