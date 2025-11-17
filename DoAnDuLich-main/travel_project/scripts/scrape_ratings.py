#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scrape additional ratings from external sources (Wikipedia, TripAdvisor, Google reviews).
This script fetches ratings and merges them with existing places_index.json.

For demo purposes, we'll use:
1. Wikipedia API to get basic info (no ratings but helps verify place exists)
2. Google Maps API (requires API key - optional)
3. Mock scraper for TripAdvisor (or use their unofficial API)

For now, we'll use a combination of Wikipedia + mock ratings to enhance data.
"""
import json
import random
import sys
import requests
from datetime import datetime

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# List of destinations to enhance
DESTINATIONS = [
    "Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Đà Lạt", "Phú Quốc",
    "Hạ Long", "Sapa", "Huế", "Nha Trang", "Hội An",
    "Cần Thơ", "Quy Nhơn", "Bà Nà Hills", "Tam Đảo"
]


def fetch_wikipedia_info(place_name):
    """Fetch basic info from Wikipedia to verify place and get description."""
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": place_name,
            "prop": "extracts",
            "explaintext": True,
            "exintro": True
        }
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "extract" in page:
                return page["extract"][:200]  # first 200 chars as summary
    except Exception as e:
        print(f"  Wikipedia fetch failed for {place_name}: {e}")
    return None


def mock_scrape_tripadviser_rating(place_name):
    """
    Mock scraper for TripAdvisor ratings.
    In production, use Selenium or TripAdvisor API.
    For now, return realistic random rating based on place popularity.
    """
    # Some places are more popular/highly rated than others
    base_ratings = {
        "Hà Nội": 4.5, "Phú Quốc": 4.6, "Hạ Long": 4.7,
        "Hội An": 4.6, "Đà Lạt": 4.5, "Hồ Chí Minh": 4.3,
        "Nha Trang": 4.4, "Sapa": 4.5, "Huế": 4.4, "Cần Thơ": 4.0
    }
    base = base_ratings.get(place_name, 4.2)
    # add slight variation
    rating = max(3.5, min(5.0, base + random.uniform(-0.2, 0.3)))
    review_count = random.randint(500, 10000)
    return {"rating": round(rating, 1), "review_count": review_count, "source": "TripAdvisor"}


def mock_scrape_google_rating(place_name):
    """Mock scraper for Google Maps ratings."""
    base_ratings = {
        "Hà Nội": 4.4, "Phú Quốc": 4.5, "Hạ Long": 4.6,
        "Hội An": 4.7, "Đà Lạt": 4.5, "Hồ Chí Minh": 4.2
    }
    base = base_ratings.get(place_name, 4.1)
    rating = max(3.5, min(5.0, base + random.uniform(-0.15, 0.25)))
    review_count = random.randint(800, 15000)
    return {"rating": round(rating, 1), "review_count": review_count, "source": "Google Maps"}


def enhance_places_index(input_file="data/places_index.json", output_file="data/places_index_enhanced.json"):
    """Load existing places index and enhance with scraped ratings."""
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        places = json.load(f)

    print(f"Loaded {len(places)} places. Enhancing with external ratings...")

    for i, place in enumerate(places):
        name = place.get("name", "")
        print(f"\n[{i+1}/{len(places)}] Processing: {name}")

        # Fetch Wikipedia info if not present
        if not place.get("description"):
            wiki_info = fetch_wikipedia_info(name)
            if wiki_info:
                place["description"] = wiki_info
                print(f"  ✓ Added Wikipedia description")

        # Scrape TripAdvisor-style ratings
        ta_rating = mock_scrape_tripadviser_rating(name)
        place["tripadviser_rating"] = ta_rating["rating"]
        place["tripadviser_reviews"] = ta_rating["review_count"]
        print(f"  ✓ TripAdvisor: {ta_rating['rating']}★ ({ta_rating['review_count']} reviews)")

        # Scrape Google-style ratings
        gm_rating = mock_scrape_google_rating(name)
        place["google_rating"] = gm_rating["rating"]
        place["google_reviews"] = gm_rating["review_count"]
        print(f"  ✓ Google: {gm_rating['rating']}★ ({gm_rating['review_count']} reviews)")

        # Compute aggregate rating (average of all sources)
        ratings = [
            float(place.get("rating", 0)) or 0,
            ta_rating["rating"],
            gm_rating["rating"]
        ]
        ratings = [r for r in ratings if r > 0]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            place["aggregate_rating"] = round(avg_rating, 1)
            place["rating_sources"] = len(ratings)
            print(f"  ✓ Aggregate rating: {avg_rating:.1f}★")

    # Save enhanced index
    print(f"\nSaving enhanced index to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(places, f, ensure_ascii=False, indent=2)
    print(f"✓ Enhanced index saved with {len(places)} places.")
    print(f"\nNext step: Use {output_file} to update training data and retrain LTR model.")


if __name__ == "__main__":
    enhance_places_index()
