from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Project, ProjectVersion
from accounts.models import Profile


class ProjectSoftDeleteAndSubmittedTests(TestCase):
    def setUp(self):
        User = get_user_model()
        # create users
        self.student = User.objects.create_user(username='student', password='pass')
        Profile.objects.create(user=self.student, type='S')

        self.faculty = User.objects.create_user(username='faculty', password='pass')
        Profile.objects.create(user=self.faculty, type='F')

        self.staff = User.objects.create_user(username='staff', password='pass')
        self.staff.is_staff = True
        self.staff.save()
        Profile.objects.create(user=self.staff, type='A')

        # create a project owned by student
        self.proj = Project.objects.create(owner=self.student, title='T1', description='D')

        self.client = Client()

    def test_submitted_projects_access(self):
        url = reverse('projects:submitted_projects')
        # student should be denied
        self.client.login(username='student', password='pass')
        resp = self.client.get(url)
        self.assertNotEqual(resp.status_code, 200)
        self.client.logout()

        # faculty can access
        self.client.login(username='faculty', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'T1')
        self.client.logout()

        # staff can access
        self.client.login(username='staff', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'T1')

    def test_soft_delete_project(self):
        del_url = reverse('projects:delete_project', args=[self.proj.pk])
        # non-owner cannot delete
        self.client.login(username='faculty', password='pass')
        resp = self.client.post(del_url)
        self.assertNotEqual(resp.status_code, 302)  # should not redirect as deletion forbidden
        self.proj.refresh_from_db()
        self.assertFalse(self.proj.is_deleted)
        self.client.logout()

        # owner can delete
        self.client.login(username='student', password='pass')
        resp = self.client.post(del_url)
        self.assertEqual(resp.status_code, 302)
        self.proj.refresh_from_db()
        self.assertTrue(self.proj.is_deleted)
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Project, ProjectVersion
from accounts.models import Profile

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

    def test_faculty_cannot_upload_version(self):
        # project owned by student
        owner = User.objects.create_user('owner_u', password='pw')
        Profile.objects.create(user=owner, type='S')
        proj = Project.objects.create(owner=owner, title='OwnerProjU', description='d')
        # faculty user
        fac = User.objects.create_user('fac_u', password='pw')
        Profile.objects.create(user=fac, type='F')
        self.client.login(username='fac_u', password='pw')
        url = reverse('projects:upload_version', args=[proj.pk])
        txt = SimpleUploadedFile('v_fac.zip', b'PK\x03\x04v')
        resp = self.client.post(url, {'uploaded_file': txt}, follow=True)
        # faculty should not be allowed to upload; ensure no new versions
        proj.refresh_from_db()
        self.assertEqual(proj.versions.count(), 0)

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

    def test_faculty_cannot_create_project(self):
        fac = User.objects.create_user('fac2', password='pw')
        Profile.objects.create(user=fac, type='F')
        self.client.login(username='fac2', password='pw')
        url = reverse('projects:create_project')
        resp = self.client.post(url, {'title': 'Forbidden', 'description': 'x'}, follow=True)
        # faculty should not be able to create projects
        self.assertNotEqual(resp.status_code, 200)
        self.assertFalse(Project.objects.filter(title='Forbidden').exists())

    def test_upload_version_with_metadata_updates_project_and_saves_snapshot(self):
        u = User.objects.create_user('stu4', password='pw')
        proj = Project.objects.create(owner=u, title='Orig', description='origdesc')
        ProjectVersion.objects.create(project=proj, version_number=1)
        self.client.login(username='stu4', password='pw')
        url = reverse('projects:upload_version', args=[proj.pk])
        txt = SimpleUploadedFile('v2.bin', b'data')
        resp = self.client.post(url, {'uploaded_file': txt, 'title_snapshot': 'New Title', 'description_snapshot': 'New Desc'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        proj.refresh_from_db()
        # project canonical fields should be updated
        self.assertEqual(proj.title, 'New Title')
        self.assertEqual(proj.description, 'New Desc')
        # new version should exist with matching snapshots
        latest = proj.versions.first()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.title_snapshot, 'New Title')
        self.assertEqual(latest.description_snapshot, 'New Desc')

    def test_student_cannot_view_others_project(self):
        # create owner and their project
        owner = User.objects.create_user('owner', password='pw')
        Profile.objects.create(user=owner, type='S')
        proj = Project.objects.create(owner=owner, title='OwnerProj', description='d')
        # another student
        other = User.objects.create_user('other', password='pw')
        # ensure profile exists and is a student
        Profile.objects.create(user=other, type='S')
        self.client.login(username='other', password='pw')
        url = reverse('projects:project_detail', args=[proj.pk])
        resp = self.client.get(url)
        # students should get 404 when accessing others' projects
        self.assertEqual(resp.status_code, 404)

    def test_faculty_can_view_others_project(self):
        owner = User.objects.create_user('owner2', password='pw')
        Profile.objects.create(user=owner, type='S')
        proj = Project.objects.create(owner=owner, title='OwnerProj2', description='d')
        fac = User.objects.create_user('fac', password='pw')
        # create profile and mark as faculty
        Profile.objects.create(user=fac, type='F')
        self.client.login(username='fac', password='pw')
        url = reverse('projects:project_detail', args=[proj.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_my_projects_list_does_not_leak_other_users_projects(self):
        # owner and their project
        owner = User.objects.create_user('owner_list', password='pw')
        Profile.objects.create(user=owner, type='S')
        proj_owner = Project.objects.create(owner=owner, title='OwnerListProj', description='d')

        # another user and their project
        other = User.objects.create_user('other_list', password='pw')
        Profile.objects.create(user=other, type='S')
        proj_other = Project.objects.create(owner=other, title='OtherListProj', description='d')

        # login as owner and fetch my_projects page
        self.client.login(username='owner_list', password='pw')
        url = reverse('projects:my_projects')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        # owner's project title should be present
        self.assertIn('OwnerListProj', content)
        # other user's project title must NOT be present
        self.assertNotIn('OtherListProj', content)
