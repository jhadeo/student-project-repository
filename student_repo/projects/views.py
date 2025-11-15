from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import is_profile_type, is_staff_or_type, require_role, forbid_role
from .models import Project, ProjectVersion
from .forms import ProjectForm, ProjectVersionForm
from .forms import ReviewForm
from django.http import FileResponse
import mimetypes
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render


@login_required
def my_projects(request):
    # exclude soft-deleted projects
    projects = Project.objects.filter(owner=request.user, is_deleted=False).order_by('-created_at')
    return render(request, 'projects/my_projects.html', {'projects': projects})


@login_required
@forbid_role('F', redirect_to='dashboard_faculty', message='Access denied: faculty may not create project submissions.')
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
    if proj.is_deleted:
        raise Http404
    # Allow owners, staff, and faculty to view a project. Students can only view their own.
    is_faculty = is_profile_type(request.user, 'F')
    if proj.owner != request.user and not (request.user.is_staff or is_faculty):
        raise Http404
    versions = proj.versions.all()
    file_form = ProjectVersionForm()
    # Pair each review with the latest project version that existed at the
    # time the review was created. This lets us show which version was
    # approved/rejected without changing the Review model.
    reviews = proj.reviews.all()
    reviews_with_versions = []
    for r in reviews:
        # Prefer an explicit FK if present (new migration); otherwise infer by timestamp
        v = getattr(r, 'version', None)
        if not v:
            v = proj.versions.filter(created_at__lte=r.created_at).first()
        reviews_with_versions.append((r, v))
    # determine whether the current user may upload versions: owners and staff only
    can_upload = (proj.owner == request.user) or request.user.is_staff
    return render(request, 'projects/project_detail.html', {
        'project': proj,
        'versions': versions,
        'file_form': file_form,
        'can_upload': can_upload,
        'is_faculty': is_faculty,
        'reviews_with_versions': reviews_with_versions,
    })


@login_required
@require_role('A', message='Access denied: admin only.')
def admin_override_status(request, pk):
    """Allow admins/staff to set a project's status by creating a review.

    Creating a Review is used to record the override and keep the audit trail.
    """
    proj = get_object_or_404(Project, pk=pk)
    if proj.is_deleted:
        raise Http404
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.project = proj
            review.reviewer = request.user
            # If no explicit version provided, attach the current latest version
            if not review.version:
                review.version = proj.latest_version
            review.save()
            messages.success(request, 'Admin override applied.')
        else:
            messages.error(request, 'Invalid data for override.')
    return redirect('projects:project_detail', pk=proj.pk)


@login_required
@require_role('F', message='Access denied: faculty only.')
def search_projects(request):
    """Simple search and filter for projects.

    Query params:
    - q: text to search in title or owner username
    - status: one of 'Approved', 'Rejected', 'Pending' to filter by computed status
    """
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    created_after = request.GET.get('created_after', '').strip()
    created_before = request.GET.get('created_before', '').strip()

    qs = Project.objects.filter(is_deleted=False).order_by('-created_at')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(owner__username__icontains=q) | Q(description__icontains=q))

    # date range filtering (optional)
    try:
        if created_after:
            qs = qs.filter(created_at__gte=created_after)
        if created_before:
            qs = qs.filter(created_at__lte=created_before)
    except Exception:
        # If parsing/filtering fails, ignore the date filters
        pass

    projects = list(qs)
    if status:
        projects = [p for p in projects if p.status == status]

    # If this is an AJAX/XHR request, return a partial (table rows) to update dynamically
    is_xhr = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if is_xhr:
        return render(request, 'projects/_submitted_projects_list.html', {'projects': projects})

    return render(request, 'projects/submitted_projects.html', {
        'projects': projects,
        'q': q,
        'status': status,
        'created_after': created_after,
        'created_before': created_before,
    })

@login_required
def download_version(request, pk, version_pk):
    """Serve a project's version file after access checks.

    This avoids linking directly to media URLs which may expose missing-file tracebacks
    and centralizes permission checks.
    """
    proj = get_object_or_404(Project, pk=pk)
    if proj.is_deleted:
        raise Http404
    is_faculty = is_profile_type(request.user, 'F')
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
@forbid_role('F', redirect_to='dashboard_faculty', message='Access denied: faculty may not upload project versions.')
def upload_version(request, pk):
    proj = get_object_or_404(Project, pk=pk)
    if proj.is_deleted:
        raise Http404
    # Students may only upload to their own projects; staff may upload to any.
    # Students may only upload to their own projects; staff may upload to any.
    if proj.owner != request.user and not request.user.is_staff:
        raise Http404
    if request.method == 'POST':
        form = ProjectVersionForm(request.POST, request.FILES)
        if form.is_valid():
            # Prevent uploads when the project is already approved (unless staff).
            # This enforces the rule: once a project is approved it cannot be edited/uploaded
            # further by the owner. If the owner wants to resubmit, a reviewer must
            # revoke approval or staff intervene.
            try:
                status = proj.status
            except Exception:
                status = None
            if status == 'Approved' and not request.user.is_staff:
                messages.error(request, 'Cannot upload: project already approved.')
                return redirect('projects:project_detail', pk=proj.pk)
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


@login_required
@require_role('F', message='Access denied: only faculty or staff may review projects.')
def review_project(request, pk):
    """Allow faculty or staff to submit a review for a project.

    Students are not allowed to review. After saving the review, redirect back
    to the project detail.
    """
    proj = get_object_or_404(Project, pk=pk)
    if proj.is_deleted:
        raise Http404
    # Prevent project owners from reviewing their own submissions
    if request.user == proj.owner:
        messages.error(request, 'Owners may not review their own projects.')
        return redirect('projects:project_detail', pk=proj.pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.project = proj
            review.reviewer = request.user
            review.save()
            messages.success(request, 'Review submitted.')
            return redirect('projects:project_detail', pk=proj.pk)
        else:
            messages.error(request, 'Invalid review submission.')
            return redirect('projects:project_detail', pk=proj.pk)
    # GET should redirect to project detail
    return redirect('projects:project_detail', pk=proj.pk)


@login_required
@require_role('F', raise_404=True)
def submitted_projects(request):
    """List all submitted (non-deleted) projects for faculty/admin."""
    projects = Project.objects.filter(is_deleted=False).order_by('-created_at')
    return render(request, 'projects/submitted_projects.html', {'projects': projects})


@login_required
def delete_project(request, pk):
    """Soft-delete a project. Owners and staff can perform this action."""
    proj = get_object_or_404(Project, pk=pk)
    # Only owner or staff can delete. Faculty may not delete others' projects.
    if proj.owner != request.user and not request.user.is_staff:
        raise Http404
    if request.method == 'POST':
        proj.soft_delete()
        messages.success(request, 'Project deleted (soft delete).')
        return redirect('projects:my_projects')
    return render(request, 'projects/confirm_delete.html', {'project': proj})
