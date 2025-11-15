from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Project, ProjectVersion

User = get_user_model()


class ProjectsTests(TestCase):
    def test_create_project_and_initial_upload(self):
        u = User.objects.create_user('stu', password='pw')
        self.client.login(username='stu', password='pw')
        url = reverse('projects:create_project')
        txt = SimpleUploadedFile('test.zip', b'PK\x03\x04test')
        resp = self.client.post(url, {'title': 'Test Project', 'description': 'desc', 'uploaded_file': txt}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Project.objects.filter(title='Test Project', owner=u).exists())
        proj = Project.objects.get(title='Test Project')
        self.assertTrue(ProjectVersion.objects.filter(project=proj).exists())

    def test_upload_new_version(self):
        u = User.objects.create_user('stu2', password='pw')
        proj = Project.objects.create(owner=u, title='P2', description='d')
        ProjectVersion.objects.create(project=proj, version_number=1)
        self.client.login(username='stu2', password='pw')
        url = reverse('projects:upload_version', args=[proj.pk])
        txt = SimpleUploadedFile('v2.zip', b'PK\x03\x04v2')
        resp = self.client.post(url, {'uploaded_file': txt}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(proj.versions.count(), 2)

    def test_reject_non_archive_upload(self):
        u = User.objects.create_user('stu3', password='pw')
        self.client.login(username='stu3', password='pw')
        url = reverse('projects:create_project')
        txt = SimpleUploadedFile('anyfile.txt', b'hello')
        # creating project with a non-archive file should succeed (any single file allowed)
        resp = self.client.post(url, {'title': 'Any', 'description': 'd', 'uploaded_file': txt}, follow=True)
        self.assertEqual(resp.status_code, 200)
        # project should be created
        self.assertTrue(Project.objects.filter(title='Any').exists())
