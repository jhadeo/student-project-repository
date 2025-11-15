from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # soft-delete flag and timestamp for UC-10 and auditability
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.owner.username})"

    def soft_delete(self):
        """Soft-delete the project instead of hard removing it from the DB."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @property
    def latest_version(self):
        """Return the latest ProjectVersion instance or None."""
        # versions are ordered by -version_number then -created_at
        return self.versions.first()


class ProjectVersion(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='versions')
    uploaded_file = models.FileField(upload_to='project_uploads/', blank=True, null=True)
    version_number = models.PositiveIntegerField(default=1)
    title_snapshot = models.CharField(max_length=200, blank=True)
    description_snapshot = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number', '-created_at']

    def __str__(self):
        return f"{self.project.title} v{self.version_number}"
