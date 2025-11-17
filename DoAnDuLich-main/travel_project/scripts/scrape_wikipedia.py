"""
Simple Wikipedia crawler to extract place names from a given page.
Usage:
  python scripts/scrape_wikipedia.py --url "https://vi.wikipedia.org/…" --out data/places.csv

This script collects anchor text and link hrefs from the main content area.
"""
import requests
from bs4 import BeautifulSoup
import csv
import argparse
from urllib.parse import urljoin


def scrape(url, out_csv):
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # Try common content selectors used by Wikipedia
    content = soup.select_one('#mw-content-text') or soup.select_one('.mw-parser-output') or soup.body

    items = []
    if content:
        for a in content.find_all('a'):
            text = a.get_text(strip=True)
            href = a.get('href')
            if not text:
                continue
            # skip internal anchors and citations
            if href and href.startswith('#'):
                continue
            # only absolute or /wiki/ links
            if href and (href.startswith('/wiki/') or href.startswith('http')):
                full = urljoin(url, href)
                items.append((text, full))

    # Deduplicate by text
    seen = set()
    uniq = []
    for name, link in items:
        if name in seen:
            continue
        seen.add(name)
        uniq.append((name, link))

    # write csv
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'source_url'])
        for name, link in uniq:
            writer.writerow([name, link])

    print(f"Wrote {len(uniq)} items to {out_csv}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='Wikipedia page URL')
    parser.add_argument('--out', default='data/places.csv', help='Output CSV file')
    args = parser.parse_args()
    scrape(args.url, args.out)
