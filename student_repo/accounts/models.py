from django.conf import settings
from django.db import models

class AccType(models.TextChoices):
    STUDENT = 'S', 'Student'
    FACULTY = 'F', 'Faculty'
    ADMIN = 'A', 'Admin'

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, blank=True)
    # Do not allow NULL in DB (null=False). Keep blank=True so forms
    # may leave the type empty (app logic treats empty as 'unset').
    type = models.CharField(max_length=1, choices=AccType.choices, blank=True, null=False)

    def __str__(self):
        return f"{self.user.username} profile"

    def save(self, *args, **kwargs):
        """Protect against removing the last admin.

        If this Profile currently is the only admin (type 'A') and an update
        tries to change its type away from 'A', preserve 'A' instead.
        This is a defensive, model-level invariant so other code paths
        (admin, views, etc.) cannot accidentally demote the last admin.
        """
        # prevent NULL being stored in DB; normalize None to empty string
        if self.type is None:
            self.type = ''

        try:
            # if this profile exists in DB, inspect previous value
            if self.pk:
                prev = Profile.objects.filter(pk=self.pk).first()
                if prev and prev.type == 'A' and self.type != 'A':
                    # count current admin profiles (including prev)
                    admin_count = Profile.objects.filter(type='A').count()
                    if admin_count <= 1:
                        # preserve admin status to avoid leaving zero admins
                        self.type = 'A'
        except Exception:
            # be defensive: on any DB error, fall back to saving as-is
            pass
        super().save(*args, **kwargs)