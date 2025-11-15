from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import Profile


class AccountsTests(TestCase):
    def test_register_and_profile_created(self):
        resp = self.client.post(reverse('register'), {
            'username': 'tuser', 'email': 't@example.com', 'password1': 'strongpass123', 'password2': 'strongpass123'
        }, follow=True)
        # Registration logs the user in and the post-login dispatcher should
        # send users without a type set to the profile page by default.
        self.assertEqual(resp.request['PATH_INFO'], reverse('profile'))
        u = User.objects.get(username='tuser')
        self.assertTrue(hasattr(u, 'profile'))

    def test_login(self):
        User.objects.create_user('u1', email='u1@example.com', password='pw12345')
        resp = self.client.post(reverse('login'), {'username': 'u1', 'password': 'pw12345'}, follow=True)
        # no profile.type set -> should land on profile page
        self.assertEqual(resp.request['PATH_INFO'], reverse('profile'))

    def test_profile_update(self):
        u = User.objects.create_user('u2', email='u2@example.com', password='pw12345')
        self.client.login(username='u2', password='pw12345')
        resp = self.client.post(reverse('profile'), {'full_name': 'New Name', 'type': 'S'})
        self.assertRedirects(resp, reverse('profile'))
        u.refresh_from_db()
        self.assertEqual(u.profile.full_name, 'New Name')

    def test_password_change(self):
        u = User.objects.create_user('u3', email='u3@example.com', password='oldpass')
        self.client.login(username='u3', password='oldpass')
        resp = self.client.post(reverse('profile'), {
            'old_password': 'oldpass',
            'new_password1': 'newstrongpass1',
            'new_password2': 'newstrongpass1',
            'change_password': '1'
        })
        # password change should redirect to profile
        self.assertRedirects(resp, reverse('profile'))
        u.refresh_from_db()
        self.assertTrue(u.check_password('newstrongpass1'))
    
    def test_login_redirect_to_dashboards(self):
        # Student
        u = User.objects.create_user('stu', email='stu@example.com', password='pw')
        Profile.objects.create(user=u, type='S')
        resp = self.client.post(reverse('login'), {'username': 'stu', 'password': 'pw'}, follow=True)
        self.assertEqual(resp.request['PATH_INFO'], reverse('dashboard_student'))

        # Faculty
        v = User.objects.create_user('fac', email='fac@example.com', password='pw')
        Profile.objects.create(user=v, type='F')
        resp = self.client.post(reverse('login'), {'username': 'fac', 'password': 'pw'}, follow=True)
        self.assertEqual(resp.request['PATH_INFO'], reverse('dashboard_faculty'))

        # Admin via profile type
        a = User.objects.create_user('adm', email='adm@example.com', password='pw')
        Profile.objects.create(user=a, type='A')
        resp = self.client.post(reverse('login'), {'username': 'adm', 'password': 'pw'}, follow=True)
        self.assertEqual(resp.request['PATH_INFO'], reverse('dashboard_admin'))

        # Staff user (is_staff) should also land on admin dashboard
        s = User.objects.create_user('staffu', email='staff@example.com', password='pw')
        s.is_staff = True
        s.save()
        resp = self.client.post(reverse('login'), {'username': 'staffu', 'password': 'pw'}, follow=True)
        self.assertEqual(resp.request['PATH_INFO'], reverse('dashboard_admin'))
 
