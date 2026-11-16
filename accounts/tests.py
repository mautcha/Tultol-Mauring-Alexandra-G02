from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.forms import RegistrationForm, LoginForm


class AccountAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.dashboard_url = reverse('dashboard:home')
        
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
        """Landing page (/) redirects unauthenticated visitors to registration."""
        response = self.client.get('/')
        self.assertRedirects(response, self.register_url)

    def test_registration_page_loads(self):
        """GET request loads the registration form successfully."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        self.assertIn('form', response.context)

    def test_successful_registration_redirects_to_login(self):
        """Valid registration creates user with hashed password and redirects to login."""
        response = self.client.post(self.register_url, self.valid_reg_data, follow=True)
        
        # User created in database
        self.assertTrue(User.objects.filter(username='cebushopper').exists())
        user = User.objects.get(username='cebushopper')
        
        # Passwords must be hashed using Django's built-in PBKDF2/SHA256, NEVER plain-text
        self.assertNotEqual(user.password, 'SecurePassword123!')
        self.assertTrue(user.check_password('SecurePassword123!'))
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))

        # Redirects to login page with success message
        self.assertRedirects(response, self.login_url)
        messages = list(response.context['messages'])
        self.assertTrue(any("created" in str(m).lower() for m in messages))

    def test_registration_validation_errors(self):
        """Ensure required fields and duplicate checks work."""
        # Empty fields
        form = RegistrationForm(data={'username': '', 'email': '', 'password': '', 'password_confirm': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('password', form.errors)

        # Mismatched passwords
        mismatch_data = self.valid_reg_data.copy()
        mismatch_data['password_confirm'] = 'DifferentPassword123!'
        response = self.client.post(self.register_url, mismatch_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('password_confirm', response.context['form'].errors)

    def test_duplicate_username_and_email_rejected(self):
        """Duplicate username or email must be rejected."""
        User.objects.create_user(username='existinguser', email='existing@example.com', password='Password123!')
        
        # Duplicate username
        data = self.valid_reg_data.copy()
        data['username'] = 'EXISTINGUSER'
        response = self.client.post(self.register_url, data)
        self.assertIn('username', response.context['form'].errors)

        # Duplicate email
        data = self.valid_reg_data.copy()
        data['username'] = 'newuniqueuser'
        data['email'] = 'EXISTING@EXAMPLE.COM'
        response = self.client.post(self.register_url, data)
        self.assertIn('email', response.context['form'].errors)

    # --- Login Tests ---

    def test_login_page_loads(self):
        """GET request loads the login form successfully."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertIn('form', response.context)

    def test_successful_login_with_username(self):
        """Registered user can log in with username and access the dashboard."""
        User.objects.create_user(username='malluser', email='malluser@example.com', password='ValidPassword123!')
        
        response = self.client.post(self.login_url, {
            'username': 'malluser',
            'password': 'ValidPassword123!'
        }, follow=True)

        self.assertRedirects(response, self.dashboard_url)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'malluser')
        messages = list(response.context['messages'])
        self.assertTrue(any("welcome back" in str(m).lower() for m in messages))

    def test_successful_login_with_email(self):
        """Registered user can also log in using their email address."""
        User.objects.create_user(username='emailshopper', email='shopper@mall.ph', password='ValidPassword123!')
        
        response = self.client.post(self.login_url, {
            'username': 'shopper@mall.ph',
            'password': 'ValidPassword123!'
        }, follow=True)

        self.assertRedirects(response, self.dashboard_url)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'emailshopper')

    def test_invalid_credentials_show_error(self):
        """Invalid username or password shows clear error message."""
        User.objects.create_user(username='legituser', email='legit@example.com', password='CorrectPassword123!')
        
        response = self.client.post(self.login_url, {
            'username': 'legituser',
            'password': 'WrongPassword999!'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        messages = list(response.context['messages'])
        self.assertTrue(any("invalid" in str(m).lower() for m in messages))

    # --- Logout Tests ---

    def test_logout_ends_session_and_redirects(self):
        """Logging out ends user session and redirects to login with message."""
        user = User.objects.create_user(username='logoutuser', email='logout@example.com', password='Password123!')
        self.client.login(username='logoutuser', password='Password123!')

        response = self.client.get(self.logout_url, follow=True)
        self.assertRedirects(response, self.login_url)
        self.assertFalse(response.context['user'].is_authenticated)
        messages = list(response.context['messages'])
        self.assertTrue(any("logged out" in str(m).lower() for m in messages))

    # --- Protected Pages (@login_required) Tests ---

    def test_protected_dashboard_redirects_unauthenticated_user(self):
        """Unauthenticated user accessing protected dashboard is redirected to login."""
        response = self.client.get(self.dashboard_url)
        expected_redirect = f"{self.login_url}?next={self.dashboard_url}"
        self.assertRedirects(response, expected_redirect)

    def test_protected_dashboard_accessible_to_logged_in_user(self):
        """Authenticated user can access the dashboard."""
        User.objects.create_user(username='authshopper', email='auth@example.com', password='Password123!')
        self.client.login(username='authshopper', password='Password123!')

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/home.html')
        self.assertContains(response, 'authshopper')

    def test_login_redirects_to_next_parameter(self):
        """After login, user is redirected back to the originally requested protected URL."""
        User.objects.create_user(username='nextshopper', email='next@example.com', password='Password123!')
        
        login_with_next_url = f"{self.login_url}?next={self.dashboard_url}"
        response = self.client.post(login_with_next_url, {
            'username': 'nextshopper',
            'password': 'Password123!'
        }, follow=True)

        self.assertRedirects(response, self.dashboard_url)
