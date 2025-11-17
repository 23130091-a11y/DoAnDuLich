"""
FastAPI app exposing /api/suggest?q=... endpoint.
It will try to query Elasticsearch if available; otherwise it uses the fallback JSON file `data/places_index.json`.
The model `model.pkl` will be loaded if present and used to re-rank candidates.
Results are cached in Redis for improved performance.

Run with:
  uvicorn fastapi_app.app:app --reload --port 8001

Then call: GET http://localhost:8001/api/suggest?q=da+lat
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=os.getenv('FASTAPI_LOG_LEVEL', 'info').upper())
logger = logging.getLogger(__name__)

try:
    from elasticsearch import Elasticsearch
    ES_AVAILABLE = True
except Exception:
    ES_AVAILABLE = False

import joblib
from rapidfuzz import fuzz
from fastapi_app.cache import init_redis, get_cache_stats, invalidate_cache

app = FastAPI(title='Suggest API - Travel Search')

# Allow our Django frontend (running on port 8000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

MODEL = None
INDEX_DATA = None
REDIS_CLIENT = None


def normalize_text(s: str) -> str:
    """Normalize text: remove diacritics, lower-case, collapse whitespace."""
    import unicodedata, re
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r'\s+', ' ', s).strip()
    return s


@app.on_event('startup')
def load_resources():
    global MODEL, INDEX_DATA, REDIS_CLIENT
    
    # Initialize Redis if enabled
    enable_caching = os.getenv('ENABLE_CACHING', 'True').lower() == 'true'
    if enable_caching:
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        REDIS_CLIENT = init_redis(host=redis_host, port=redis_port)
    
    # load model if present
    if os.path.exists('model.pkl'):
        try:
            MODEL = joblib.load('model.pkl')
            logger.info('✓ Loaded model.pkl')
        except Exception as e:
            logger.error(f'Failed to load model.pkl: {e}')
    
    # fallback: load simple json-model with weights
    if MODEL is None and os.path.exists('model.json'):
        try:
            with open('model.json', 'r', encoding='utf-8') as mf:
                MODEL = json.load(mf)
                logger.info('✓ Loaded model.json (weights)')
        except Exception as e:
            logger.error(f'Failed to load model.json: {e}')
    
    # load fallback index: prefer enhanced version with external ratings
    index_path = 'data/places_index_enhanced.json' if os.path.exists('data/places_index_enhanced.json') else 'data/places_index.json'
    if os.path.exists(index_path):
        with open(index_path, encoding='utf-8') as f:
            INDEX_DATA = json.load(f)
        logger.info(f'✓ Loaded index from {index_path}')
        # precompute normalized name for faster matching
        for d in INDEX_DATA:
            try:
                d['norm_name'] = normalize_text(d.get('name', ''))
            except Exception:
                d['norm_name'] = d.get('name', '')


class SuggestItem(BaseModel):
    name: str
    score: float
    rating: float = 0.0
    review_count: int = 0


@app.get('/api/suggest', response_model=List[SuggestItem])
def suggest(q: str = Query(..., min_length=1)):
    """
    Suggest destinations based on query.
    Results are cached in Redis for 1 hour.
    """
    # Check cache first
    if REDIS_CLIENT:
        from fastapi_app.cache import get_cache_key
        cache_key = get_cache_key("suggest", q)
        try:
            cached = REDIS_CLIENT.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT: {cache_key}")
                return json.loads(cached)
        except Exception as e:
            logger.debug(f"Cache GET failed: {e}")
    
    # Retrieval: try ES first (if available and healthy)
    candidates = []
    es_ok = False
    if ES_AVAILABLE and os.getenv('ENABLE_ELASTICSEARCH', 'False').lower() == 'true':
        try:
            es = Elasticsearch(['http://localhost:9200'], request_timeout=2)
            if es.ping(request_timeout=2):
                es_ok = True
                body = {
                    'query': {
                        'multi_match': {
                            'query': q,
                            'fields': ['name^3'],
                            'fuzziness': 'AUTO'
                        }
                    },
                    'size': 50
                }
                res = es.search(index='places', body=body)
                for hit in res['hits']['hits']:
                    src = hit['_source']
                    candidates.append({
                        'name': src.get('name'),
                        'es_score': hit['_score'],
                        'rating': float(src.get('rating', 0) or 0),
                        'review_count': int(src.get('review_count', 0) or 0)
                    })
        except Exception as e:
            logger.debug(f'ES not available: {e}')

    # Fallback: local fuzzy scan
    if not candidates or not es_ok:
        if not INDEX_DATA:
            raise HTTPException(status_code=500, detail='No index available')
        q_norm = normalize_text(q)
        for d in INDEX_DATA:
            name = d.get('name', '')
            if not name:
                continue
            norm_name = d.get('norm_name') or normalize_text(name)
            es_score = fuzz.token_set_ratio(q_norm, norm_name) / 100.0
            candidates.append({
                'name': name,
                'es_score': es_score,
                'rating': float(d.get('rating', 0) or 0),
                'review_count': int(d.get('review_count', 0) or 0)
            })
        # sort by es_score desc and take 50
        candidates.sort(key=lambda x: x['es_score'], reverse=True)
        candidates = candidates[:50]

    # Ranking: prepare features for model or fall back to simple combination
    # Normalize features: es_score in [0,1], rating scaled to [0,1], review_count scaled to [0,1]
    X = []
    for c in candidates:
        es_f = float(c.get('es_score', 0) or 0)
        rating_f = float(c.get('rating', 0) or 0) / 5.0
        rc = int(c.get('review_count', 0) or 0)
        # scale review_count: cap at 5000 (common high) and normalize
        rc_f = min(1.0, rc / 5000.0)
        X.append([es_f, rating_f, rc_f])

    scores = None
    if MODEL is not None:
        try:
            # If MODEL is a scikit-learn estimator
            if hasattr(MODEL, 'predict'):
                scores = MODEL.predict(X)
            # If MODEL is a simple dict with weights
            elif isinstance(MODEL, dict) and 'weights' in MODEL:
                w = MODEL.get('weights', [0.6, 0.25, 0.15])
                b = MODEL.get('intercept', 0.0)
                scores = [(x[0]*w[0] + x[1]*w[1] + x[2]*w[2] + b) for x in X]
            else:
                scores = None
        except Exception as e:
            logger.error(f'Model predict failed: {e}')

    items = []
    for i, c in enumerate(candidates):
        if scores is not None:
            score = float(scores[i])
        else:
            # Default heuristic (use same normalization as X)
            es_f = float(c.get('es_score', 0) or 0)
            rating_f = float(c.get('rating', 0) or 0) / 5.0
            rc_f = min(1.0, int(c.get('review_count', 0) or 0) / 5000.0)
            score = (es_f * 0.6 + rating_f * 0.25 + rc_f * 0.15)
        items.append({
            'name': c['name'],
            'score': score,
            'rating': float(c.get('rating', 0) or 0),
            'review_count': int(c.get('review_count', 0) or 0)
        })

    # sort by score desc and return top 10
    items.sort(key=lambda x: x['score'], reverse=True)
    out = items[:10]
    
    # Cache result
    if REDIS_CLIENT:
        from fastapi_app.cache import get_cache_key
        cache_key = get_cache_key("suggest", q)
        ttl = int(os.getenv('REDIS_CACHE_TTL', 3600))
        try:
            REDIS_CLIENT.setex(cache_key, ttl, json.dumps(out, ensure_ascii=False))
            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
        except Exception as e:
            logger.debug(f"Cache SET failed: {e}")
    
    return out


@app.get('/api/cache/stats')
def cache_stats():
    """Get cache statistics."""
    return get_cache_stats()


@app.post('/api/cache/invalidate')
def cache_invalidate(pattern: str = "suggest:*"):
    """Invalidate cache keys matching pattern."""
    count = invalidate_cache(pattern)
    return {"invalidated": count, "pattern": pattern}


@app.get('/health')
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model_loaded": MODEL is not None,
        "index_loaded": INDEX_DATA is not None,
        "redis_connected": REDIS_CLIENT is not None
    }

