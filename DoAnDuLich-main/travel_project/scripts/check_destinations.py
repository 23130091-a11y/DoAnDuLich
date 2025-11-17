import os
import django
import sys
from pathlib import Path

# ensure project root is on sys.path so `import travel_project` works
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_project.settings')
django.setup()

from travel.models import Destination

qs = Destination.objects.all()
print('Count:', qs.count())
print('Names:', list(qs.values_list('name', flat=True)))
