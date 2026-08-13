import sys
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Verifies PostgreSQL database connection and custom User model setup."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("--- FinTrack Day 1 System Verification ---"))

        # 1. Database Connection Check
        try:
            connection.ensure_connection()
            db_name = connection.settings_dict.get('NAME')
            db_engine = connection.settings_dict.get('ENGINE')
            self.stdout.write(
                self.style.SUCCESS(f"✓ PostgreSQL Connection Successful: Database '{db_name}' using {db_engine}")
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"✗ PostgreSQL Connection Failed: {e}"))
            sys.exit(1)

        # 2. Custom User Model Check
        try:
            User = get_user_model()
            user_count = User.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f"✓ Custom User Model Recognized: '{User._meta.label}' (Total users: {user_count})")
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"✗ Custom User Model Verification Failed: {e}"))
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS("\n✓ Day 1 Backend Foundation Verification Passed!"))
