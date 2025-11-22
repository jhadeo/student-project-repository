from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, AccType


User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    # expose profile type on the registration form (exclude Admin 'A')
    type = forms.ChoiceField(choices=[(k, v) for k, v in AccType.choices if k != 'A'], required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already in use.")
        return email

    def save(self, commit=True):
        # create the User first
        user = super().save(commit=commit)
        # attach or create the Profile and save selected type
        type_value = self.cleaned_data.get('type', '')
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.type = type_value
        profile.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        # include 'type' so admin can change account types via dropdown
        fields = ('full_name', 'type')
    
    def save(self, commit=True):
        """Preserve existing `type` when the field is disabled or missing.

        Some views disable the `type` field (so it's not posted). Without
        special handling, a bound form missing `type` can clear the value
        on save. Ensure we keep the instance value when that happens.
        """
        # remember the original value before the ModelForm mutates it
        original_type = getattr(self.instance, 'type', None)

        # call parent to get the instance updated from cleaned_data
        instance = super().save(commit=False)

        # If the field is disabled on the form it won't be present in
        # POST data — preserve the original value from the instance
        # provided to the form (if any).
        try:
            field_disabled = self.fields['type'].disabled
        except Exception:
            field_disabled = False

        # If the field is disabled on the form it won't be present in
        # POST data — preserve the original value from the instance
        # provided to the form (if any).
        if field_disabled and getattr(self, 'instance', None):
            instance.type = original_type

        # Browsers don't submit disabled fields. If the bound POST data
        # doesn't contain the 'type' key at all, the form would otherwise
        # clear the value; detect that and preserve the original.
        try:
            data_has_type = 'type' in (getattr(self, 'data', {}) or {})
        except Exception:
            data_has_type = False

        if not data_has_type and getattr(self, 'instance', None):
            instance.type = original_type

        if commit:
            instance.save()
        return instance

from django.contrib.auth import get_user_model

User = get_user_model()


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')
