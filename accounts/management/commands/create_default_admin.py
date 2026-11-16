import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from accounts.models import Profile


class Command(BaseCommand):
    help = "Create or update the default Mall Admin account from environment variables or CLI flags."

    def add_arguments(self, parser):
        parser.add_argument('--username', default=os.environ.get('ADMIN_USERNAME', 'admin'))
        parser.add_argument('--email', default=os.environ.get('ADMIN_EMAIL', 'admin@tultol.local'))
        parser.add_argument('--password', default=os.environ.get('ADMIN_PASSWORD', ''))

    def handle(self, *args, **options):
        username = options['username'].strip()
        email = options['email'].strip()
        password = options['password']

        if not password:
            raise CommandError(
                "Admin password is required. Set ADMIN_PASSWORD in .env or pass --password."
            )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True},
        )
        user.email = email
        user.is_staff = True
        user.set_password(password)
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = 'admin'
        profile.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} Mall Admin account '{username}'."))
