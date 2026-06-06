import csv
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


INPUT_CSV = ".csv"          # your existing CSV with post URLs
OUTPUT_CSV = ".csv"          # direct mp4 links only
OUTPUT_TXT = ".txt"          # direct mp4 links only

POST_URL_COLUMN = "url"               # change if your CSV column is named differently
POST_TEXT_COLUMN = "post_text"        # optional, from earlier script

DELAY_SECONDS = 1

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def extract_mp4_from_post(post_url):
    response = requests.get(post_url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Most direct target based on your example:
    source = soup.select_one('div[data-setup] video source[src$=".mp4"]')

    # Fallback: any video source mp4 on the page
    if not source:
        source = soup.select_one('video source[src$=".mp4"]')

    # Broader fallback: any source tag with mp4 in src
    if not source:
        source = soup.select_one('source[src*=".mp4"]')

    if not source:
        return ""

    src = source.get("src", "").strip()
    return urljoin(post_url, src)


def main():
    input_path = Path(INPUT_CSV)

    if not input_path.exists():
        raise FileNotFoundError(f"Could not find {INPUT_CSV}")

    results = []
    seen_mp4s = set()

    with open(INPUT_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader, start=1):
            post_url = row.get(POST_URL_COLUMN, "").strip()
            post_text = row.get(POST_TEXT_COLUMN, "").strip()

            if not post_url:
                continue

            print(f"[{i}] Checking post: {post_url}")

            try:
                mp4_url = extract_mp4_from_post(post_url)

                if not mp4_url:
                    print("    No MP4 found")
                    continue

                if mp4_url in seen_mp4s:
                    print("    Duplicate MP4 skipped")
                    continue

                seen_mp4s.add(mp4_url)

                results.append({
                    "post_text": post_text,
                    "post_url": post_url,
                    "mp4_url": mp4_url
                })

                print(f"    Found: {mp4_url}")

            except Exception as e:
                print(f"    Error: {e}")

            time.sleep(DELAY_SECONDS)

    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["post_text", "post_url", "mp4_url"])
        writer.writeheader()
        writer.writerows(results)

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        for row in results:
            f.write(row["mp4_url"] + "\n")

    print(f"\nSaved {len(results)} MP4 links to:")
    print(f" - {OUTPUT_CSV}")
    print(f" - {OUTPUT_TXT}")


if __name__ == "__main__":
    main()
