import datetime
from django.core.management.base import BaseCommand, CommandError
from transactions.services import NotificationService


class Command(BaseCommand):
    help = 'Processes budgets, financial goals, and recurring transactions to generate financial notifications and alerts.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Target processing date in YYYY-MM-DD format (defaults to current date).'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Filter processing for a specific user ID.'
        )

    def handle(self, *args, **options):
        target_date = None
        date_str = options.get('date')
        if date_str:
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError("Invalid date format. Expected YYYY-MM-DD.")

        user_id = options.get('user_id')
        user = None
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise CommandError(f"User with ID {user_id} does not exist.")

        results = NotificationService.process_all_financial_alerts(
            user=user,
            target_date=target_date
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed financial notifications for {results['target_date']}:\n"
                f"  - Notifications created: {results['alerts_created_count']}\n"
                f"  - Budgets inspected: {results['budgets_processed_count']}\n"
                f"  - Goals inspected: {results['goals_processed_count']}\n"
                f"  - Recurring schedules inspected: {results['recurring_processed_count']}"
            )
        )
