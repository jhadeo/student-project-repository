from django.contrib import admin
from .models import Profile

# Register your models here.


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'type')
    search_fields = ('user__username', 'user__email', 'full_name')
    list_filter = ('type',)