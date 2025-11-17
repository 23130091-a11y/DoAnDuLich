from django.contrib import admin
# Register your models here.
from .models import Destination


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
	list_display = ("name", "folder", "created_at")
	prepopulated_fields = {"slug": ("name",)}
	search_fields = ("name", "description")

# Register your models here.
