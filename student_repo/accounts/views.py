from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, ProfileForm, UserForm
from .models import Profile
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
            return redirect('profile')
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
                if not request.user.is_staff:
                    # preserve existing type
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
                    profile_form.save()
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
                profile_form.save()
                messages.success(request, 'Account and profile updated successfully.')
                return redirect('profile')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    # disable 'type' editing for non-staff in the rendered form
    if not request.user.is_staff:
        try:
            profile_form.fields['type'].disabled = True
        except Exception:
            pass
    pwd_form = PasswordChangeForm(request.user)
    return render(request, 'accounts/profile.html', {'profile': profile, 'user_form': user_form, 'form': profile_form, 'pwd_form': pwd_form})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Allow logout via GET or POST and redirect to LOGOUT_REDIRECT_URL or login."""
    auth_logout(request)
    redirect_to = getattr(settings, 'LOGOUT_REDIRECT_URL', None) or 'login'
    return redirect(redirect_to)
from django.shortcuts import render

# Create your views here.
