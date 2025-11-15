from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, ProfileForm, UserForm
from .models import Profile, AccType
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import logout as auth_logout
from django.conf import settings
from django.views.decorators.http import require_http_methods


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # ensure profile exists
            Profile.objects.get_or_create(user=user)
            # authenticate so Django sets backend on the user object
            auth_user = authenticate(request, username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password1'))
            if auth_user:
                login(request, auth_user)
            # Redirect to the LOGIN_REDIRECT_URL dispatcher so users land on
            # the appropriate dashboard depending on their profile.type.
            from django.conf import settings
            return redirect(settings.LOGIN_REDIRECT_URL)
        # removed debug printing of form errors
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user = request.user
    if request.method == 'POST':
        # determine which form was submitted
        if 'save_account' in request.POST:
            user_form = UserForm(request.POST, instance=user)
            profile_form = ProfileForm(instance=profile)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Account updated successfully.')
                return redirect('profile')
        elif 'save_profile' in request.POST:
            profile_form = ProfileForm(request.POST, instance=profile)
            user_form = UserForm(instance=user)
            if profile_form.is_valid():
                # save but prevent non-staff users from changing 'type'
                pf = profile_form.save(commit=False)
                # preserve existing type when the requester is not staff
                # OR when this profile is the only admin (disabled field for sole admin)
                if (not request.user.is_staff) or (profile.type == 'A' and Profile.objects.filter(type='A').count() == 1):
                    pf.type = profile.type
                pf.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('profile')
        elif 'change_password' in request.POST:
            pwd_form = PasswordChangeForm(request.user, request.POST)
            user_form = UserForm(instance=user)
            profile_form = ProfileForm(instance=profile)
            if pwd_form.is_valid():
                user = pwd_form.save()
                # keep the user logged in after password change
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
                return redirect('profile')
        else:
            # fallback: infer intent from posted fields
            post_keys = set(request.POST.keys())
            profile_keys = {'full_name', 'type'}
            user_keys = {'username', 'email'}
            if post_keys & profile_keys:
                profile_form = ProfileForm(request.POST, instance=profile)
                user_form = UserForm(instance=user)
                if profile_form.is_valid():
                    # preserve existing type for non-staff or sole-admin (prevent blanking)
                    pf = profile_form.save(commit=False)
                    if (not request.user.is_staff) or (profile.type == 'A' and Profile.objects.filter(type='A').count() == 1):
                        pf.type = profile.type
                    pf.save()
                    messages.success(request, 'Profile updated successfully.')
                    return redirect('profile')
            elif post_keys & user_keys:
                user_form = UserForm(request.POST, instance=user)
                profile_form = ProfileForm(instance=profile)
                if user_form.is_valid():
                    user_form.save()
                    messages.success(request, 'Account updated successfully.')
                    return redirect('profile')
            else:
                # try both as a last resort
                user_form = UserForm(request.POST, instance=user)
                profile_form = ProfileForm(request.POST, instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                # preserve existing type for non-staff or sole-admin to avoid accidentally removing admin
                pf = profile_form.save(commit=False)
                if (not request.user.is_staff) or (profile.type == 'A' and Profile.objects.filter(type='A').count() == 1):
                    pf.type = profile.type
                pf.save()
                messages.success(request, 'Account and profile updated successfully.')
                return redirect('profile')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    # disable 'type' editing for non-staff in the rendered form
    # disable 'type' editing for non-staff in the rendered form
    if not request.user.is_staff:
        try:
            profile_form.fields['type'].disabled = True
        except Exception:
            pass
    # additionally, if this user is the only admin, even staff cannot change their own type
    try:
        if profile.type == 'A' and Profile.objects.filter(type='A').count() == 1:
            profile_form.fields['type'].disabled = True
    except Exception:
        pass
    pwd_form = PasswordChangeForm(request.user)
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'user_form': user_form,
        'form': profile_form,
        'pwd_form': pwd_form,
        'acc_types': AccType.choices,
    })


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Allow logout via GET or POST and redirect to LOGOUT_REDIRECT_URL or login."""
    auth_logout(request)
    redirect_to = getattr(settings, 'LOGOUT_REDIRECT_URL', None) or 'login'
    return redirect(redirect_to)
from django.shortcuts import render


# Dashboards
@login_required
def student_dashboard(request):
    """Simple student dashboard. Only accessible to users with Profile.type == 'S'."""
    profile = getattr(request.user, 'profile', None)
    if profile and profile.type == 'S':
        context = {
            'profile': profile,
            'usecases': [
                'UC-01: Accounts & Profiles',
                'UC-06: Project submission (student-facing)',
                'UC-13: View feedback/reviews'
            ]
        }
        return render(request, 'accounts/dashboards/student_dashboard.html', context)
    messages.error(request, 'Access denied: student dashboard only.')
    return redirect('profile')


@login_required
def faculty_dashboard(request):
    """Simple faculty dashboard. Accessible to users with Profile.type == 'F' or staff."""
    profile = getattr(request.user, 'profile', None)
    if request.user.is_staff or (profile and profile.type == 'F'):
        context = {
            'profile': profile,
            'usecases': [
                'UC-11..UC-17: Review workflow',
                'UC-18: Search & Filter submissions',
                'UC-21: Notifications (placeholder)'
            ]
        }
        return render(request, 'accounts/dashboards/faculty_dashboard.html', context)
    messages.error(request, 'Access denied: faculty dashboard only.')
    return redirect('profile')


@login_required
def admin_dashboard(request):
    """Admin dashboard. Requires staff privileges or Profile.type == 'A'."""
    profile = getattr(request.user, 'profile', None)
    if request.user.is_staff or (profile and profile.type == 'A'):
        context = {
            'profile': profile,
            'usecases': [
                'UC-25..UC-28: Ops, backups, audit logs',
                'UC-22: Reporting & aggregates',
                'UC-27: Soft deletes / audit trail'
            ]
        }
        return render(request, 'accounts/dashboards/admin_dashboard.html', context)
    messages.error(request, 'Access denied: admin dashboard only.')
    return redirect('profile')

# Create your views here.


@login_required
def manage_users(request):
    """List users for admin management (UC-04)."""
    if not request.user.is_staff:
        messages.error(request, 'Access denied: admin only.')
        return redirect('profile')
    User = get_user_model()
    users = User.objects.all().order_by('username')
    # number of admin profiles (type 'A') to protect sole admin
    admin_count = Profile.objects.filter(type='A').count()
    return render(request, 'accounts/manage_users.html', {'users': users, 'admin_count': admin_count})


@login_required
def edit_user(request, user_id):
    """Edit a user's basic info and profile. Admin-only (UC-04)."""
    if not request.user.is_staff:
        messages.error(request, 'Access denied: admin only.')
        return redirect('profile')
    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        messages.error(request, 'User not found.')
        return redirect('accounts:manage_users')
    profile, _ = Profile.objects.get_or_create(user=user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            pf = profile_form.save(commit=False)
            # protect sole admin: if the target is currently the only admin,
            # do not allow changing their type away from 'A'
            if profile.type == 'A' and Profile.objects.filter(type='A').count() == 1:
                pf.type = 'A'
            pf.save()
            messages.success(request, 'User updated.')
            return redirect('accounts:manage_users')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    # If the target user is the only admin, disable the 'type' dropdown so it cannot be changed
    try:
        if profile.type == 'A' and Profile.objects.filter(type='A').count() == 1:
            profile_form.fields['type'].disabled = True
    except Exception:
        pass
    disable_type = False
    try:
        if profile.type == 'A' and Profile.objects.filter(type='A').count() == 1:
            disable_type = True
    except Exception:
        pass
    return render(request, 'accounts/edit_user.html', {
        'user_obj': user,
        'user_form': user_form,
        'profile_form': profile_form,
        'acc_types': AccType.choices,
        'profile': profile,
        'disable_type': disable_type,
    })


@login_required
def delete_user(request, user_id):
    """Delete a user (admin-only). This performs a hard delete via Django ORM."""
    if not request.user.is_staff:
        messages.error(request, 'Access denied: admin only.')
        return redirect('profile')
    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        messages.error(request, 'User not found.')
        return redirect('accounts:manage_users')
    if request.method == 'POST':
        # prevent deleting the sole admin account
        target_profile = Profile.objects.filter(user=user).first()
        if target_profile and target_profile.type == 'A' and Profile.objects.filter(type='A').count() == 1:
            messages.error(request, 'Cannot delete the only admin account.')
            return redirect('accounts:manage_users')
        username = str(user.username)
        user.delete()
        messages.success(request, f'User {username} deleted.')
        return redirect('accounts:manage_users')
    return render(request, 'accounts/confirm_delete_user.html', {'user_obj': user})


def post_login_redirect(request):
    """Redirect user after login to the appropriate dashboard based on Profile.type.

    Falls back to the `profile` page when no type is set.
    """
    # If anonymous somehow reaches here, send to login
    if not request.user.is_authenticated:
        from django.shortcuts import resolve_url
        return redirect('login')

    profile = getattr(request.user, 'profile', None)
    # Student
    if profile and profile.type == 'S':
        return redirect('dashboard_student')
    # Faculty
    if profile and profile.type == 'F':
        return redirect('dashboard_faculty')
    # Admin (explicit)
    if profile and profile.type == 'A':
        return redirect('dashboard_admin')
    # Staff users also get admin dashboard
    if request.user.is_staff:
        return redirect('dashboard_admin')

    # Default fallback
    return redirect('profile')
