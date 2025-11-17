#!/usr/bin/env python
"""
Import destinations from places_index_full.json into Django DB.
Usage: python scripts/import_json_to_db.py
"""
import os
import sys
import json
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_project.settings')
django.setup()

from travel.models import Destination

def import_destinations(json_file='data/places_index_full.json'):
    """Import destinations from JSON file into DB."""
    filepath = os.path.join(os.path.dirname(__file__), '..', json_file)
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} destinations from {json_file}")
    
    created_count = 0
    updated_count = 0
    
    for item in data:
        name = item.get('name')
        if not name:
            print(f"  Skipping item with no name: {item}")
            continue
        
        # Try to get or create
        obj, created = Destination.objects.get_or_create(
            name=name,
            defaults={
                'description': item.get('description', ''),
                'folder': item.get('folder', ''),
            }
        )
        
        # Update fields even if exists
        obj.description = item.get('description', obj.description)
        obj.folder = item.get('folder', obj.folder)
        obj.save()
        
        if created:
            created_count += 1
            print(f"  ✓ Created: {name}")
        else:
            updated_count += 1
            print(f"  ~ Updated: {name}")
    
    print(f"\n=== Import Complete ===")
    print(f"Created: {created_count}")
    print(f"Updated: {updated_count}")
    print(f"Total in DB: {Destination.objects.count()}")

if __name__ == '__main__':
    import_destinations()
