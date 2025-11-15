from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountsTests(TestCase):
    def test_register_and_profile_created(self):
        resp = self.client.post(reverse('register'), {
            'username': 'tuser', 'email': 't@example.com', 'password1': 'strongpass123', 'password2': 'strongpass123'
        })
        self.assertRedirects(resp, reverse('profile'))
        u = User.objects.get(username='tuser')
        self.assertTrue(hasattr(u, 'profile'))

    def test_login(self):
        User.objects.create_user('u1', email='u1@example.com', password='pw12345')
        resp = self.client.post(reverse('login'), {'username': 'u1', 'password': 'pw12345'})
        self.assertEqual(resp.status_code, 302)

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
from django.test import TestCase

# Create your tests here.
