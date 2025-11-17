import os
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Destination
import unicodedata
import re


def normalize_text(s: str) -> str:
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def home(request):
    # Keep existing behavior: build cards from static image folders
    base_path = os.path.join(settings.BASE_DIR, 'travel', 'static', 'images')
    results = []

    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)
        if os.path.isdir(folder_path):
            images = [
                f"{folder}/{img}" for img in os.listdir(folder_path)
                if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
            ]

            if images:
                results.append({
                    "name": folder.title(),
                    "desc": f"Khám phá vẻ đẹp của {folder.title()}",
                    "images": images,
                    "folder": folder,
                    "img": images[0]
                })

    return render(request, 'travel/index.html', {"results": results})


@require_GET
def search_suggestions(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'results': []})
    qn = normalize_text(q)
    matches = []
    for d in Destination.objects.all():
        name = d.name or ''
        if qn in normalize_text(name):
            matches.append(name)
            if len(matches) >= 10:
                break
    return JsonResponse({'results': matches})


@require_GET
def search_results(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        qn = normalize_text(q)
        # naive accent-insensitive matching by scanning all records (OK for small demo DB)
        for d in Destination.objects.all():
            name = d.name or ''
            desc = d.description or ''
            if qn in normalize_text(name) or qn in normalize_text(desc):
                # Attempt to collect images from static folder
                images = []
                base_path = os.path.join(settings.BASE_DIR, 'travel', 'static', 'images')
                folder_path = os.path.join(base_path, d.folder)
                if os.path.isdir(folder_path):
                    images = [f"{d.folder}/{img}" for img in os.listdir(folder_path) if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]

                results.append({
                    'name': d.name,
                    'desc': d.description or f'Khám phá vẻ đẹp của {d.name}',
                    'images': images,
                    'folder': d.folder,
                })

    return render(request, 'travel/search_results.html', {'query': q, 'results': results})
