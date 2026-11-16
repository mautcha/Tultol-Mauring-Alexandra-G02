from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class RoleDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.shopper_url = reverse('dashboard:shopper_dashboard')
        self.admin_url = reverse('dashboard:admin_dashboard')

        self.shopper = User.objects.create_user(
            username='shopper1', email='shopper1@example.com', password='Password123!'
        )
        self.admin = User.objects.create_user(
            username='admin1', email='admin1@example.com', password='Password123!', is_staff=True
        )
        self.admin.profile.role = 'admin'
        self.admin.profile.save()

    def test_dashboards_require_login(self):
        for url in (self.shopper_url, self.admin_url):
            resp = self.client.get(url)
            self.assertRedirects(resp, f"{self.login_url}?next={url}")

    def test_shopper_can_open_shopper_dashboard_but_not_admin_dashboard(self):
        self.client.login(username='shopper1', password='Password123!')

        ok_resp = self.client.get(self.shopper_url)
        self.assertEqual(ok_resp.status_code, 200)
        self.assertTemplateUsed(ok_resp, 'dashboard/shopper.html')

        blocked_resp = self.client.get(self.admin_url, follow=True)
        self.assertRedirects(blocked_resp, self.shopper_url)
        msgs = list(blocked_resp.context['messages'])
        self.assertTrue(any('permission' in str(m).lower() for m in msgs))

    def test_admin_can_open_admin_dashboard_but_not_shopper_dashboard(self):
        self.client.login(username='admin1', password='Password123!')

        ok_resp = self.client.get(self.admin_url)
        self.assertEqual(ok_resp.status_code, 200)
        self.assertTemplateUsed(ok_resp, 'dashboard/admin.html')

        blocked_resp = self.client.get(self.shopper_url, follow=True)
        self.assertRedirects(blocked_resp, self.admin_url)
        msgs = list(blocked_resp.context['messages'])
        self.assertTrue(any('permission' in str(m).lower() for m in msgs))
