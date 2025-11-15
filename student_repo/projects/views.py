from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Project, ProjectVersion
from .forms import ProjectForm, ProjectVersionForm
from django.http import FileResponse
import mimetypes


@login_required
def my_projects(request):
    projects = Project.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'projects/my_projects.html', {'projects': projects})


@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        file_form = ProjectVersionForm(request.POST, request.FILES)
        if form.is_valid() and file_form.is_valid():
            proj = form.save(commit=False)
            proj.owner = request.user
            proj.save()
            # create initial version if file uploaded
            uploaded = file_form.cleaned_data.get('uploaded_file')
            if uploaded:
                # prefer explicit snapshots from the upload form; fall back to project fields
                title_snap = file_form.cleaned_data.get('title_snapshot') or proj.title
                desc_snap = file_form.cleaned_data.get('description_snapshot') or proj.description
                ProjectVersion.objects.create(
                    project=proj,
                    uploaded_file=uploaded,
                    version_number=1,
                    title_snapshot=title_snap,
                    description_snapshot=desc_snap,
                )
            messages.success(request, 'Project created successfully.')
            return redirect('projects:project_detail', pk=proj.pk)
    else:
        form = ProjectForm()
        file_form = ProjectVersionForm()
    return render(request, 'projects/create_project.html', {'form': form, 'file_form': file_form})


@login_required
def project_detail(request, pk):
    proj = get_object_or_404(Project, pk=pk)
    # Allow owners, staff, and faculty to view a project. Students can only view their own.
    profile = getattr(request.user, 'profile', None)
    is_faculty = bool(profile and getattr(profile, 'type', None) == 'F')
    if proj.owner != request.user and not (request.user.is_staff or is_faculty):
        raise Http404
    versions = proj.versions.all()
    file_form = ProjectVersionForm()
    return render(request, 'projects/project_detail.html', {'project': proj, 'versions': versions, 'file_form': file_form})

@login_required
def download_version(request, pk, version_pk):
    """Serve a project's version file after access checks.

    This avoids linking directly to media URLs which may expose missing-file tracebacks
    and centralizes permission checks.
    """
    proj = get_object_or_404(Project, pk=pk)
    profile = getattr(request.user, 'profile', None)
    is_faculty = bool(profile and getattr(profile, 'type', None) == 'F')
    if proj.owner != request.user and not (request.user.is_staff or is_faculty):
        raise Http404

    version = get_object_or_404(ProjectVersion, pk=version_pk, project=proj)
    ffield = version.uploaded_file
    if not ffield or not ffield.name:
        raise Http404("File not found")

    storage = ffield.storage
    if not storage.exists(ffield.name):
        # File missing on disk/storage
        raise Http404("File not found")

    # Use storage.open to get a file-like object and return a FileResponse
    fileobj = storage.open(ffield.name, 'rb')
    content_type, _ = mimetypes.guess_type(ffield.name)
    response = FileResponse(fileobj, content_type=content_type or 'application/octet-stream')
    response['Content-Length'] = storage.size(ffield.name)
    # Suggest a filename for download
    response['Content-Disposition'] = f'attachment; filename="{ffield.name.split("/")[-1]}"'
    return response


@login_required
def upload_version(request, pk):
    proj = get_object_or_404(Project, pk=pk)
    # Allow owners, staff, and faculty to upload a version. Students can only upload to their own projects.
    profile = getattr(request.user, 'profile', None)
    is_faculty = bool(profile and getattr(profile, 'type', None) == 'F')
    if proj.owner != request.user and not (request.user.is_staff or is_faculty):
        raise Http404
    if request.method == 'POST':
        form = ProjectVersionForm(request.POST, request.FILES)
        if form.is_valid():
            # calculate next version number
            latest = proj.versions.first()
            next_ver = (latest.version_number + 1) if latest else 1
            pv = form.save(commit=False)
            pv.project = proj
            pv.version_number = next_ver
            # If title/description snapshots were provided, use them. Also update
            # the canonical Project title/description to reflect the newest metadata.
            title_snap = form.cleaned_data.get('title_snapshot')
            desc_snap = form.cleaned_data.get('description_snapshot')
            if title_snap:
                pv.title_snapshot = title_snap
                if proj.title != title_snap:
                    proj.title = title_snap
            if desc_snap:
                pv.description_snapshot = desc_snap
                if proj.description != desc_snap:
                    proj.description = desc_snap
            pv.save()
            # save project if metadata changed
            proj.save()
            messages.success(request, 'New version uploaded and project metadata updated.')
        else:
            messages.error(request, 'Upload failed.')
    return redirect('projects:project_detail', pk=proj.pk)
