#!/usr/bin/env python
"""Run suggest() directly by importing FastAPI app module (no HTTP server required).
This calls load_resources() to ensure INDEX_DATA and MODEL are initialized, then calls suggest() function.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi_app import app as fastapi_module
from fastapi_app.app import load_resources, suggest

# call startup loader to populate INDEX_DATA
load_resources()

queries = ['da lat', 'Đà Lạt', 'ha noi', 'phu quoc', 'my son', 'trang an', 'sapa']

for q in queries:
    print('\nQuery:', q)
    try:
        result = suggest(q=q)
        for i, it in enumerate(result, 1):
            print(f"  {i}. {it['name']} — score={it['score']:.4f} rating={it.get('rating')} reviews={it.get('review_count')}")
    except Exception as e:
        print('  Error calling suggest():', e)
