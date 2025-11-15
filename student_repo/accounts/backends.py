from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authenticate using either username or email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        users = UserModel.objects.filter(username__iexact=username)
        if not users.exists():
            users = UserModel.objects.filter(email__iexact=username)
        for user in users:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
