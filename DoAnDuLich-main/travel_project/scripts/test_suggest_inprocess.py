#!/usr/bin/env python
"""In-process test client for FastAPI `app` using TestClient.
This avoids running uvicorn and tests the API handlers directly.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from fastapi_app.app import app


def test(queries):
    with TestClient(app) as client:
        for q in queries:
            r = client.get('/api/suggest', params={'q': q})
            print('\nQuery:', q)
            if r.status_code != 200:
                print('  HTTP', r.status_code, r.text[:200])
                continue
            data = r.json()
            for i, it in enumerate(data[:10], 1):
                print(f"  {i}. {it.get('name')} — score={it.get('score'):.4f} rating={it.get('rating')} reviews={it.get('review_count')}")


if __name__ == '__main__':
    queries = [
        'da lat', 'Đà Lạt', 'ha noi', 'phu quoc', 'hoian', 'nha trang', 'my son', 'trang an', 'sapa'
    ]
    test(queries)
