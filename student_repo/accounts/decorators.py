from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import Http404


def _get_profile_type(user):
    profile = getattr(user, 'profile', None)
    return getattr(profile, 'type', '') if profile is not None else ''


def is_profile_type(user, type_char: str) -> bool:
    """Return True if the given user has a Profile.type equal to type_char."""
    return _get_profile_type(user) == type_char


def is_staff_or_type(user, type_char: str) -> bool:
    """Return True if user.is_staff or their profile.type matches type_char."""
    return bool(user and (getattr(user, 'is_staff', False) or is_profile_type(user, type_char)))


def require_role(type_char: str = None, redirect_to: str = 'profile', message: str = None, raise_404: bool = False):
    """Decorator factory that requires the requesting user to have the given profile type
    or be staff. If not allowed, either redirect with a flash message or raise Http404.

    - type_char: one of 'S', 'F', 'A' or None. If None and raise_404 is False the decorator
      becomes a no-op (useful for symmetry).
    - redirect_to: named url to redirect unauthorized users to (when raise_404 is False).
    - message: optional flash message on redirect.
    - raise_404: if True, raise Http404 instead of redirecting.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            # staff bypass
            if getattr(request.user, 'is_staff', False):
                return view_func(request, *args, **kwargs)
            if type_char is None:
                return view_func(request, *args, **kwargs)
            if is_profile_type(request.user, type_char):
                return view_func(request, *args, **kwargs)
            # unauthorized
            if raise_404:
                raise Http404
            if message:
                messages.error(request, message)
            return redirect(redirect_to)
        return _wrapped
    return decorator


def forbid_role(type_char: str, redirect_to: str = 'profile', message: str = None):
    """Decorator factory that forbids users with the given profile type (unless staff).
    If the user has that type and is not staff, redirect with message.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            # staff always allowed
            if getattr(request.user, 'is_staff', False):
                return view_func(request, *args, **kwargs)
            if is_profile_type(request.user, type_char):
                if message:
                    messages.error(request, message)
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
