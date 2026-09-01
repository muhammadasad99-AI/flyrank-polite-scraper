import requests

try:
    resp = requests.get("https://books.toscrape.com/robots.txt", timeout=15)
    print("Status:", resp.status_code)
    print("Content:", repr(resp.text))
except requests.exceptions.RequestException as e:
    print("Request failed:", e)