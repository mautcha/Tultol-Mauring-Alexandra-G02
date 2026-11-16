from io import BytesIO
from PIL import Image
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.forms import RegistrationForm


def make_test_image(name='avatar.png', size=(20, 20)):
    buf = BytesIO()
    Image.new('RGB', size, color='teal').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/png')


class AccountAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.profile_url = reverse('accounts:profile')
        self.profile_edit_url = reverse('accounts:profile_edit')
        self.change_password_url = reverse('accounts:change_password')
        self.password_reset_url = reverse('accounts:password_reset')
        self.shopper_dashboard_url = reverse('dashboard:shopper_dashboard')
        self.admin_dashboard_url = reverse('dashboard:admin_dashboard')

        self.valid_reg_data = {
            'username': 'cebushopper',
            'email': 'shopper@example.com',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
        }

    # --- Registration Tests ---

    def test_root_landing_page_redirects_to_register(self):
        response = self.client.get('/')
        self.assertRedirects(response, self.register_url)

    def test_registration_page_loads_without_role_field(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        self.assertNotIn('role', response.context['form'].fields)

    def test_successful_registration_creates_shopper_with_hashed_password(self):
        data = self.valid_reg_data.copy()
        data['role'] = 'admin'  # Attempted privilege escalation must be ignored
        response = self.client.post(self.register_url, data, follow=True)

        user = User.objects.get(username='cebushopper')
        self.assertNotEqual(user.password, 'SecurePassword123!')
        self.assertTrue(user.check_password('SecurePassword123!'))
        self.assertEqual(user.profile.role, 'shopper')
        self.assertFalse(user.is_staff)
        self.assertRedirects(response, self.login_url)

    def test_registration_validation_errors(self):
        form = RegistrationForm(data={'username': '', 'email': '', 'password': '', 'password_confirm': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('password', form.errors)

        mismatch_data = self.valid_reg_data.copy()
        mismatch_data['password_confirm'] = 'DifferentPassword123!'
        response = self.client.post(self.register_url, mismatch_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('password_confirm', response.context['form'].errors)

    def test_duplicate_username_and_email_rejected(self):
        User.objects.create_user(username='existinguser', email='existing@example.com', password='Password123!')

        data = self.valid_reg_data.copy()
        data['username'] = 'EXISTINGUSER'
        response = self.client.post(self.register_url, data)
        self.assertIn('username', response.context['form'].errors)

        data = self.valid_reg_data.copy()
        data['username'] = 'newuniqueuser'
        data['email'] = 'EXISTING@EXAMPLE.COM'
        response = self.client.post(self.register_url, data)
        self.assertIn('email', response.context['form'].errors)

    # --- Login & Logout Tests ---

    def test_successful_login_with_username_redirects_to_shopper_dashboard(self):
        User.objects.create_user(username='malluser', email='malluser@example.com', password='ValidPassword123!')

        response = self.client.post(self.login_url, {
            'username': 'malluser',
            'password': 'ValidPassword123!',
        }, follow=True)

        self.assertRedirects(response, self.shopper_dashboard_url)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_successful_login_with_email(self):
        User.objects.create_user(username='emailshopper', email='shopper@mall.ph', password='ValidPassword123!')

        response = self.client.post(self.login_url, {
            'username': 'shopper@mall.ph',
            'password': 'ValidPassword123!',
        }, follow=True)

        self.assertRedirects(response, self.shopper_dashboard_url)
        self.assertEqual(response.context['user'].username, 'emailshopper')

    def test_admin_login_redirects_to_admin_dashboard(self):
        admin_user = User.objects.create_user(username='malladmin', email='admin@mall.ph', password='ValidPassword123!')
        admin_user.profile.role = 'admin'
        admin_user.profile.save()

        response = self.client.post(self.login_url, {
            'username': 'malladmin',
            'password': 'ValidPassword123!',
        }, follow=True)

        self.assertRedirects(response, self.admin_dashboard_url)

    def test_invalid_credentials_show_error(self):
        User.objects.create_user(username='legituser', email='legit@example.com', password='CorrectPassword123!')

        response = self.client.post(self.login_url, {
            'username': 'legituser',
            'password': 'WrongPassword999!',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        msgs = list(response.context['messages'])
        self.assertTrue(any('invalid' in str(m).lower() for m in msgs))

    def test_login_ignores_external_next_url(self):
        User.objects.create_user(username='safeuser', email='safe@example.com', password='ValidPassword123!')

        response = self.client.post(f"{self.login_url}?next=https://evil.example.com", {
            'username': 'safeuser',
            'password': 'ValidPassword123!',
        })

        self.assertRedirects(response, self.shopper_dashboard_url)

    def test_logout_requires_post_and_ends_session(self):
        User.objects.create_user(username='logoutuser', email='logout@example.com', password='Password123!')
        self.client.login(username='logoutuser', password='Password123!')

        get_response = self.client.get(self.logout_url)
        self.assertEqual(get_response.status_code, 405)

        post_response = self.client.post(self.logout_url, follow=True)
        self.assertRedirects(post_response, self.login_url)
        self.assertFalse(post_response.context['user'].is_authenticated)

    # --- Profile Tests ---

    def test_profile_requires_login(self):
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.profile_url}")

    def test_logged_in_user_can_view_and_update_own_profile(self):
        user = User.objects.create_user(username='profuser', email='prof@example.com', password='Password123!')
        self.client.login(username='profuser', password='Password123!')

        view_resp = self.client.get(self.profile_url)
        self.assertEqual(view_resp.status_code, 200)
        self.assertContains(view_resp, 'profuser')

        edit_resp = self.client.post(self.profile_edit_url, {
            'first_name': 'Alex',
            'last_name': 'Mauring',
            'email': 'alex@example.com',
            'contact_number': '09171234567',
            'profile_photo': make_test_image(),
        }, follow=True)

        self.assertRedirects(edit_resp, self.profile_url)
        user.refresh_from_db()
        user.profile.refresh_from_db()
        self.assertEqual(user.first_name, 'Alex')
        self.assertEqual(user.email, 'alex@example.com')
        self.assertEqual(user.profile.contact_number, '09171234567')
        self.assertTrue(bool(user.profile.profile_photo))

    def test_profile_edit_rejects_duplicate_email(self):
        User.objects.create_user(username='other', email='taken@example.com', password='Password123!')
        User.objects.create_user(username='me', email='me@example.com', password='Password123!')
        self.client.login(username='me', password='Password123!')

        response = self.client.post(self.profile_edit_url, {
            'first_name': 'Me',
            'last_name': 'User',
            'email': 'TAKEN@example.com',
            'contact_number': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)

    # --- Change Password & Password Reset Tests ---

    def test_change_password_keeps_session_active(self):
        user = User.objects.create_user(username='pwuser', email='pw@example.com', password='OldPassword123!')
        self.client.login(username='pwuser', password='OldPassword123!')

        response = self.client.post(self.change_password_url, {
            'old_password': 'OldPassword123!',
            'new_password1': 'NewSecurePass456!',
            'new_password2': 'NewSecurePass456!',
        }, follow=True)

        self.assertRedirects(response, self.profile_url)
        self.assertTrue(response.context['user'].is_authenticated)
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewSecurePass456!'))

    def test_password_reset_sends_email_and_resets_password(self):
        user = User.objects.create_user(username='resetuser', email='reset@example.com', password='OldPassword123!')

        response = self.client.post(self.password_reset_url, {'email': 'reset@example.com'})
        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/accounts/password/reset/', mail.outbox[0].body)

        # Extract reset path from email body
        reset_line = [line for line in mail.outbox[0].body.splitlines() if '/accounts/password/reset/' in line][0]
        reset_path = '/' + reset_line.split('://', 1)[1].split('/', 1)[1]

        confirm_resp = self.client.post(reset_path, {
            'new_password1': 'BrandNewPass789!',
            'new_password2': 'BrandNewPass789!',
        }, follow=True)
        # First POST redirects to the token-less set-password session URL or directly completes
        if confirm_resp.status_code == 200 and 'form' in confirm_resp.context:
            confirm_resp = self.client.post(confirm_resp.request['PATH_INFO'], {
                'new_password1': 'BrandNewPass789!',
                'new_password2': 'BrandNewPass789!',
            }, follow=True)

        self.assertRedirects(confirm_resp, reverse('accounts:password_reset_complete'))
        user.refresh_from_db()
        self.assertTrue(user.check_password('BrandNewPass789!'))
