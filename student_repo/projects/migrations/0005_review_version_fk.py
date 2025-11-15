from django.db import migrations, models


def forwards(apps, schema_editor):
    Review = apps.get_model('projects', 'Review')
    ProjectVersion = apps.get_model('projects', 'ProjectVersion')
    # For each review, attach the latest version that was present at or before the review
    for review in Review.objects.all():
        try:
            v = ProjectVersion.objects.filter(project_id=review.project_id, created_at__lte=review.created_at).order_by('-created_at').first()
            if v:
                review.version_id = v.pk
                review.save(update_fields=['version_id'])
        except Exception:
            # best-effort: skip problematic rows
            continue


def backwards(apps, schema_editor):
    Review = apps.get_model('projects', 'Review')
    for review in Review.objects.all():
        review.version = None
        review.save(update_fields=['version'])


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='version',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='reviewed_by', to='projects.projectversion'),
        ),
        migrations.RunPython(forwards, backwards),
    ]
