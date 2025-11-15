from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # Intentionally do not auto-create Profile on User.save() here.
    # Tests and views in this project explicitly create or get_or_create
    # profiles where needed. Auto-creating here caused duplicate creation
    # races in some test setups, so keep the signal as a no-op for safety.
    return
