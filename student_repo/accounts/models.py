from django.conf import settings
from django.db import models

class AccType(models.TextChoices):
    STUDENT = 'S', 'Student'
    FACULTY = 'F', 'Faculty'
    ADMIN = 'A', 'Admin'

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, blank=True)
    type = models.CharField(max_length=1, choices=AccType.choices, blank=True)

    def __str__(self):
        return f"{self.user.username} profile"