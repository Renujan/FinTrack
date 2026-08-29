from django.core.management.base import BaseCommand
from transactions.backups.services import BackupService


class Command(BaseCommand):
    help = 'Processes backup retention policy, marking expired backup records and safely purging associated storage files.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting expired financial backups cleanup...'))
        count = BackupService.cleanup_expired_backups()
        self.stdout.write(self.style.SUCCESS(f'Successfully processed {count} expired backup records.'))
