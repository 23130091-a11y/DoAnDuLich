from django.db import models
from django.utils.text import slugify


# Create your models here.
class Destination(models.Model):
	name = models.CharField(max_length=200, unique=True)
	slug = models.SlugField(max_length=200, unique=True, blank=True)
	description = models.TextField(blank=True)
	# folder name under travel/static/images/<folder>/ containing images for this dest
	folder = models.CharField(max_length=200, help_text="Folder name inside static/images")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)
