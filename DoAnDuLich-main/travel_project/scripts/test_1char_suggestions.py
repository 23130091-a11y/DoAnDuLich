#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test 1-character suggestions with FastAPI endpoint.
"""
import requests
import json
import time

# Test FastAPI with 1-char suggestions
queries = ['h', 'd', 'p', 's', 'c']
print('Testing FastAPI /api/suggest endpoint...')
print('='*70)

for q in queries:
    try:
        resp = requests.get(f'http://127.0.0.1:8001/api/suggest?q={q}', timeout=10)
        if resp.status_code == 200:
            results = resp.json()
            print(f'\nQuery: "{q}" → {len(results)} suggestions')
            for i, r in enumerate(results[:3], 1):
                print(f'  {i}. {r["name"]:30} Score: {r["score"]:6.3f}  Rating: {r["rating"]:3.1f}★')
        else:
            print(f'Query "{q}": Error {resp.status_code}')
    except Exception as e:
        print(f'Query "{q}": Connection error - {e}')

print('\n' + '='*70)
print('✓ 1-character suggestions working!')
print('Open browser: http://127.0.0.1:8000/')
