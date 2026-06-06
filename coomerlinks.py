import csv
import time
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup


START_URL = ""
START_PAGE = 1
END_PAGE = 15

OUTPUT_FILE = ""

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def set_page_number(url, page_number):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    query["page"] = [str(page_number)]

    new_query = urlencode(query, doseq=True)

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))


def scrape_page(url):
    print(f"Opening: {url}")

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    model_posts = soup.select_one("section.model-posts")
    if not model_posts:
        print(f"No model-posts section found: {url}")
        return []

    results = []

    for post in model_posts.select("div.post"):
        p_tag = post.select_one("p")
        view_link = post.select_one("a.view-post")

        if not view_link:
            continue

        post_text = p_tag.get_text(" ", strip=True) if p_tag else ""
        href = view_link.get("href", "").strip()
        full_url = urljoin(url, href)

        results.append({
            "page": url,
            "post_text": post_text,
            "url": full_url
        })

    return results


def main():
    all_results = []
    seen_urls = set()

    for page_number in range(START_PAGE, END_PAGE + 1):
        url = set_page_number(START_URL, page_number)

        try:
            posts = scrape_page(url)

            for post in posts:
                if post["url"] not in seen_urls:
                    seen_urls.add(post["url"])
                    all_results.append(post)

            time.sleep(1)

        except Exception as e:
            print(f"Error scraping page {page_number}: {e}")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["page", "post_text", "url"])
        writer.writeheader()
        writer.writerows(all_results)

    print(f"Saved {len(all_results)} posts to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
