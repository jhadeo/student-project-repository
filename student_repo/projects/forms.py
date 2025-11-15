from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Project, ProjectVersion


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description']


class ProjectVersionForm(forms.ModelForm):
    class Meta:
        model = ProjectVersion
        fields = ['uploaded_file', 'title_snapshot', 'description_snapshot']

    def clean_uploaded_file(self):
        f = self.cleaned_data.get('uploaded_file')
        if not f:
            return f
        # Enforce single file (FileField accepts only one file). Do not
        # restrict by extension — accept any single file type, but enforce
        # a maximum size.
        max_bytes = getattr(settings, 'PROJECT_UPLOAD_MAX_BYTES', 10 * 1024 * 1024)
        if f.size > max_bytes:
            raise ValidationError(f'File too large. Max size is {max_bytes} bytes.')
        return f
