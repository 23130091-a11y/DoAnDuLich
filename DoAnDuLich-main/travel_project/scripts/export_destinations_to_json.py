"""
Export Destination records from Django DB into data/places_index.json used as fallback index.
Enrich with metadata from places_index_full.json if available.
"""
from pathlib import Path
import os
import sys
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_project.settings')
import django
django.setup()
from travel.models import Destination
import json

# Load metadata from full index if available
metadata_map = {}
full_index_path = BASE / 'data' / 'places_index_full.json'
if full_index_path.exists():
    try:
        with open(full_index_path, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
            for item in full_data:
                metadata_map[item.get('name')] = item
        print(f"Loaded {len(metadata_map)} metadata entries from places_index_full.json")
    except Exception as e:
        print(f"Warning: could not load metadata: {e}")

out = BASE / 'data' / 'places_index.json'
out.parent.mkdir(exist_ok=True)
rows = []
for d in Destination.objects.all():
    # Get metadata or defaults
    meta = metadata_map.get(d.name, {})
    row = {
        'id': d.id,
        'name': d.name,
        'slug': d.slug,
        'description': d.description,
        'source_url': meta.get('source_url', ''),
        'rating': meta.get('rating', 0.0),
        'review_count': meta.get('review_count', 0),
        'folder': d.folder
    }
    rows.append(row)

with open(out, 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
print('Wrote', out, 'with', len(rows), 'items')
