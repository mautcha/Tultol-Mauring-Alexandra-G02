from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.forms import RegistrationForm


class AccountRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.valid_data = {
            'username': 'cebushopper',
            'email': 'shopper@example.com',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
        }

    def test_registration_page_loads(self):
        """GET request loads the registration form successfully."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        self.assertIn('form', response.context)

    def test_successful_registration(self):
        """Valid registration creates user with hashed password and shows success message."""
        response = self.client.post(self.register_url, self.valid_data, follow=True)
        
        # User created in database
        self.assertTrue(User.objects.filter(username='cebushopper').exists())
        user = User.objects.get(username='cebushopper')
        
        # Passwords must be hashed using Django's built-in PBKDF2/SHA256, NEVER plain-text
        self.assertNotEqual(user.password, 'SecurePassword123!')
        self.assertTrue(user.check_password('SecurePassword123!'))
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        
        # Verify user attributes
        self.assertEqual(user.email, 'shopper@example.com')
        self.assertEqual(user.first_name, 'Maria')
        self.assertEqual(user.last_name, 'Santos')

        # Redirects to register page with success message
        self.assertRedirects(response, self.register_url)
        messages = list(response.context['messages'])
        self.assertTrue(any("created successfully" in str(m) for m in messages))

    def test_required_fields_validation(self):
        """Ensure username, email, password, and password_confirm are required."""
        empty_data = {
            'username': '',
            'email': '',
            'password': '',
            'password_confirm': '',
        }
        form = RegistrationForm(data=empty_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('password', form.errors)
        self.assertIn('password_confirm', form.errors)

    def test_invalid_email_format(self):
        """Invalid email formats must be rejected."""
        invalid_emails = ['not-an-email', 'shopper@', '@domain.com']
        for invalid_email in invalid_emails:
            data = self.valid_data.copy()
            data['email'] = invalid_email
            form = RegistrationForm(data=data)
            self.assertFalse(form.is_valid(), f"Failed to reject invalid email: {invalid_email}")
            self.assertIn('email', form.errors)

    def test_duplicate_username_rejected(self):
        """Duplicate username (case-insensitive) must be rejected."""
        User.objects.create_user(
            username='cebushopper',
            email='existing@example.com',
            password='Password123!'
        )

        duplicate_data = self.valid_data.copy()
        duplicate_data['username'] = 'CEBUSHOPPER'
        duplicate_data['email'] = 'newshopper@example.com'

        response = self.client.post(self.register_url, duplicate_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('username', response.context['form'].errors)
        self.assertTrue(any("already taken" in err for err in response.context['form'].errors['username']))

    def test_duplicate_email_rejected(self):
        """Duplicate email (case-insensitive) must be rejected."""
        User.objects.create_user(
            username='shopper1',
            email='shopper@example.com',
            password='Password123!'
        )

        duplicate_data = self.valid_data.copy()
        duplicate_data['username'] = 'shopper2'
        duplicate_data['email'] = 'SHOPPER@EXAMPLE.COM'

        response = self.client.post(self.register_url, duplicate_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('email', response.context['form'].errors)
        self.assertTrue(any("already registered" in err for err in response.context['form'].errors['email']))

    def test_password_mismatch_rejected(self):
        """Mismatched password and password_confirm must be rejected."""
        mismatched_data = self.valid_data.copy()
        mismatched_data['password_confirm'] = 'DifferentPassword123!'

        response = self.client.post(self.register_url, mismatched_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('password_confirm', response.context['form'].errors)
        self.assertTrue(any("do not match" in err for err in response.context['form'].errors['password_confirm']))

    def test_short_password_rejected(self):
        """Passwords that are too short must be rejected by Django's password validator."""
        short_data = self.valid_data.copy()
        short_data['password'] = 'short'
        short_data['password_confirm'] = 'short'

        response = self.client.post(self.register_url, short_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('password', response.context['form'].errors)
