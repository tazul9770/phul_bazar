from django.db import models
from django.contrib.auth.models import AbstractUser
from users.managers import CustomUserManager
from django.conf import settings

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)
    phone_num = models.CharField(max_length=15, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
class Contact(models.Model):
    email = models.EmailField()
    phone_number = models.CharField(max_length=11)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
