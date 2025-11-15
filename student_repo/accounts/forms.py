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

from django.contrib.auth import get_user_model

User = get_user_model()


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')
