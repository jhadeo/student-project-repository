from django.contrib import admin
from .models import Project, ProjectVersion, Review


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'owner__username')


@admin.register(ProjectVersion)
class ProjectVersionAdmin(admin.ModelAdmin):
    list_display = ('project', 'version_number', 'created_at')
    raw_id_fields = ('project',)
    
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('project', 'reviewer', 'decision', 'created_at')
    list_filter = ('decision', 'created_at')
    search_fields = ('project__title', 'reviewer__username', 'feedback')
