"""
Management command to process due recurring transactions and generate transactions for the scheduled date.
"""
import datetime
from django.core.management.base import BaseCommand, CommandError
from transactions.services import RecurringTransactionService


class Command(BaseCommand):
    help = 'Processes due recurring transactions and generates corresponding transaction records automatically.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Target processing date in YYYY-MM-DD format (defaults to current date).'
        )

    def handle(self, *args, **options):
        target_date = None
        date_str = options.get('date')
        if date_str:
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError("Invalid date format. Expected YYYY-MM-DD.")

        results = RecurringTransactionService.process_due_recurring_transactions(target_date=target_date)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed recurring transactions for {results['target_date']}:\n"
                f"  - Schedules processed: {results['processed_schedules_count']}\n"
                f"  - Transactions generated: {results['generated_transactions_count']}\n"
                f"  - Expired schedules: {results['expired_schedules_count']}"
            )
        )
