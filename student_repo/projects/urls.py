from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.my_projects, name='my_projects'),
    path('create/', views.create_project, name='create_project'),
    path('submitted/', views.submitted_projects, name='submitted_projects'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/delete/', views.delete_project, name='delete_project'),
    path('<int:pk>/upload/', views.upload_version, name='upload_version'),
    path('<int:pk>/review/', views.review_project, name='review_project'),
    path('<int:pk>/admin_override/', views.admin_override_status, name='admin_override_status'),
    path('search/', views.search_projects, name='search_projects'),
    path('<int:pk>/download/<int:version_pk>/', views.download_version, name='download_version'),
]
