from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search_suggestions', views.search_suggestions, name='search_suggestions'),
    path('search', views.search_results, name='search_results'),
]
