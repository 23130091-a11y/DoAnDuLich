#!/usr/bin/env python
"""Quick test client for FastAPI /api/suggest endpoint."""
import requests
import sys

def test(qs):
    url = 'http://127.0.0.1:8001/api/suggest'
    for q in qs:
        try:
            r = requests.get(url, params={'q': q}, timeout=5)
            print('\nQuery:', q)
            if r.status_code != 200:
                print('  HTTP', r.status_code, r.text[:200])
                continue
            data = r.json()
            for i, it in enumerate(data[:10], 1):
                print(f"  {i}. {it.get('name')} — score={it.get('score'):.4f} rating={it.get('rating')} reviews={it.get('review_count')}")
        except Exception as e:
            print('  Request error:', e)

if __name__ == '__main__':
    queries = [
        'da lat', 'Đà Lạt', 'ha noi', 'ha noi', 'phu quoc', 'hoian', 'nha trang', 'my son', 'trang an', 'sapa'
    ]
    if len(sys.argv) > 1:
        queries = sys.argv[1:]
    test(queries)
