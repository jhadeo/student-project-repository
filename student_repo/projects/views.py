from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Project, ProjectVersion
from .forms import ProjectForm, ProjectVersionForm


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
                ProjectVersion.objects.create(project=proj, uploaded_file=uploaded, version_number=1)
            messages.success(request, 'Project created successfully.')
            return redirect('projects:project_detail', pk=proj.pk)
    else:
        form = ProjectForm()
        file_form = ProjectVersionForm()
    return render(request, 'projects/create_project.html', {'form': form, 'file_form': file_form})


@login_required
def project_detail(request, pk):
    proj = get_object_or_404(Project, pk=pk, owner=request.user)
    versions = proj.versions.all()
    file_form = ProjectVersionForm()
    return render(request, 'projects/project_detail.html', {'project': proj, 'versions': versions, 'file_form': file_form})


@login_required
def upload_version(request, pk):
    proj = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ProjectVersionForm(request.POST, request.FILES)
        if form.is_valid():
            # calculate next version number
            latest = proj.versions.first()
            next_ver = (latest.version_number + 1) if latest else 1
            pv = form.save(commit=False)
            pv.project = proj
            pv.version_number = next_ver
            pv.save()
            messages.success(request, 'New version uploaded.')
        else:
            messages.error(request, 'Upload failed.')
    return redirect('projects:project_detail', pk=proj.pk)
