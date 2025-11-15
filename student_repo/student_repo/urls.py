"""
URL configuration for student_repo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # include the accounts app (namespaced)
    path('accounts/', include('accounts.urls')),
    # expose common account URLs at top-level names as well so templates/tests
    # that use e.g. reverse('login') or reverse('profile') work without a
    # namespace.
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/register/', accounts_views.register, name='register'),
    path('accounts/logout/', accounts_views.logout_view, name='logout'),
    path('accounts/profile/', accounts_views.profile, name='profile'),
    path('accounts/dashboard/', accounts_views.post_login_redirect, name='post_login'),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change_form.html'), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
    path('accounts/dashboard/student/', accounts_views.student_dashboard, name='dashboard_student'),
    path('accounts/dashboard/faculty/', accounts_views.faculty_dashboard, name='dashboard_faculty'),
    path('accounts/dashboard/admin/', accounts_views.admin_dashboard, name='dashboard_admin'),
    path('projects/', include('projects.urls')),
    # Home should route to a dispatcher that sends logged-in users to their
    # dashboard and anonymous users to the login page.
    path('', accounts_views.post_login_redirect, name='home'),
]

# Serve media files during development when DEBUG is True
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
