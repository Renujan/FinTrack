from django.core.management.base import BaseCommand
from transactions.exports.services import DataExportService


class Command(BaseCommand):
    help = 'Processes financial export retention policy, marking expired export records and purging associated storage files.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting expired financial exports cleanup...'))
        count = DataExportService.cleanup_expired_exports()
        self.stdout.write(self.style.SUCCESS(f'Successfully processed {count} expired export records.'))
