from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # use our wrapper logout view which accepts GET and POST
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
    # Dashboards
    path('dashboard/student/', views.student_dashboard, name='dashboard_student'),
    path('dashboard/faculty/', views.faculty_dashboard, name='dashboard_faculty'),
    path('dashboard/admin/', views.admin_dashboard, name='dashboard_admin'),
    # post-login redirect — sends users to the right dashboard/profile
    path('dashboard/', views.post_login_redirect, name='post_login'),
]
