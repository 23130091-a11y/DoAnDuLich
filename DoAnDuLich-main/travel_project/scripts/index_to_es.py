"""
Index CSV of places into Elasticsearch. If Elasticsearch is not available, write a JSON fallback file `data/places_index.json`.
Usage:
  python scripts/index_to_es.py --csv data/places.csv

Requires: elasticsearch package for Python.
"""
import csv
import json
import argparse
from elasticsearch import Elasticsearch, helpers


def load_csv(csv_path):
    docs = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            docs.append(row)
    return docs


def index_to_es(docs, index_name='places'):
    es = Elasticsearch('http://localhost:9200')
    if not es.ping():
        print('Elasticsearch not available at http://localhost:9200')
        return False

    # simple mapping
    mapping = {
        'mappings': {
            'properties': {
                'name': {'type': 'text'},
                'source_url': {'type': 'keyword'},
                'rating': {'type': 'float'},
                'review_count': {'type': 'integer'}
            }
        }
    }

    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=mapping)

    actions = []
    for i, d in enumerate(docs):
        doc = {
            'name': d.get('name'),
            'source_url': d.get('source_url'),
            'rating': float(d.get('rating') or 0),
            'review_count': int(d.get('review_count') or 0)
        }
        actions.append({'_index': index_name, '_id': i+1, '_source': doc})

    helpers.bulk(es, actions)
    print(f'Indexed {len(actions)} documents into {index_name}')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True)
    parser.add_argument('--index', default='places')
    args = parser.parse_args()
    docs = load_csv(args.csv)
    ok = False
    try:
        ok = index_to_es(docs, index_name=args.index)
    except Exception as e:
        print('Error indexing to ES:', e)

    if not ok:
        # fallback to json file for local use
        with open('data/places_index.json', 'w', encoding='utf-8') as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)
        print('Wrote fallback data/places_index.json')
