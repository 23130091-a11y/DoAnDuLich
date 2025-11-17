
import argparse
import json
import os
import random
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

try:
    from elasticsearch import Elasticsearch
    ES_AVAILABLE = True
except Exception:
    ES_AVAILABLE = False

from rapidfuzz import fuzz

SAMPLE_QUERIES = [
    'hạ long', 'ha long', 'da lat', 'da nang', 'phu quoc', 'ha noi', 'nha trang', 'sapa', 'hue', 'bien dep'
]


def load_index():
    if ES_AVAILABLE:
        es = Elasticsearch('http://localhost:9200')
        if es.ping():
            # pull all docs from index 'places'
            res = es.search(index='places', body={'query': {'match_all': {}}, 'size': 1000})
            docs = [hit['_source'] for hit in res['hits']['hits']]
            return docs
    # fallback: prefer enhanced index with external ratings
    enhanced_path = 'data/places_index_enhanced.json'
    if os.path.exists(enhanced_path):
        with open(enhanced_path, encoding='utf-8') as f:
            return json.load(f)
    with open('data/places_index.json', encoding='utf-8') as f:
        return json.load(f)


def build_training_data(docs):
    rows = []
    for q in SAMPLE_QUERIES:
        # compute fuzzy score as a proxy for ES score
        candidates = []
        for d in docs:
            name = d.get('name','')
            es_score = fuzz.token_set_ratio(q, name)/100.0
            candidates.append((name, es_score, float(d.get('rating',0)), int(d.get('review_count',0)), d))
        # sort by es_score desc and pick top 10
        candidates.sort(key=lambda x: x[1], reverse=True)
        top = candidates[:10]
        for rank, (name, es_score, rating, review_count, d) in enumerate(top):
            # heuristic label: combine es_score and rating and review_count to create pseudo-target
            target = es_score*3 + min(1.0, rating/5.0)*1.5 + (0 if review_count==0 else min(1.0, review_count/20000.0))*1.5
            # normalize target to 0-3
            target = max(0, min(3, target))
            rows.append({'query': q, 'item_name': name, 'es_score': es_score, 'rating': rating, 'review_count': review_count, 'target': target})
    df = pd.DataFrame(rows)
    return df


def train(df, out='model.pkl'):
    X = df[['es_score','rating','review_count']]
    y = df['target']
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_val)
    print('MSE:', mean_squared_error(y_val, preds))
    joblib.dump(model, out)
    print('Saved model to', out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='model.pkl')
    args = parser.parse_args()
    docs = load_index()
    print('Loaded', len(docs), 'docs')
    df = build_training_data(docs)
    print('Built training data examples:', len(df))
    train(df, out=args.out)
