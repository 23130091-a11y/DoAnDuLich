from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
# Bảng người dùng chính
class User(AbstractUser):
    last_login = None
    is_staff = None
    is_superuser = None
    username = None

    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []