from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # soft-delete flag and timestamp for auditability
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


class Review(models.Model):
    DECISION_PENDING = 'P'
    DECISION_APPROVED = 'A'
    DECISION_REJECTED = 'R'
    DECISION_CHOICES = [
        (DECISION_PENDING, 'Pending'),
        (DECISION_APPROVED, 'Approved'),
        (DECISION_REJECTED, 'Rejected'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    # explicit link to the version that was reviewed. nullable for existing data.
    version = models.ForeignKey('ProjectVersion', null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_by')
    decision = models.CharField(max_length=1, choices=DECISION_CHOICES, default=DECISION_PENDING)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review {self.get_decision_display()} by {self.reviewer.username} on {self.project.title}"


@property
def project_status(self):
    """Return the project status derived from the latest review.

    Possible values: 'Approved', 'Rejected', 'Pending', 'No Reviews'.
    """
    latest_review = self.reviews.first()
    latest_version = self.versions.first()

    # If there are no reviews, treat the project as Pending by default
    # (newly created projects should start as pending).
    if not latest_review:
        return 'Pending'

    # If a new version has been uploaded after the last review, the project
    # should be treated as pending again (student resubmitted after rejection
    # or after addressing feedback).
    if latest_version and latest_version.created_at > latest_review.created_at:
        return 'Pending'

    # Otherwise, project status is derived from the latest review decision.
    if latest_review.decision == Review.DECISION_APPROVED:
        return 'Approved'
    if latest_review.decision == Review.DECISION_REJECTED:
        return 'Rejected'
    return 'Pending'

# attach convenience property to Project class
Project.status = project_status
