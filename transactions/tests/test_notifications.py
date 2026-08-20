import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from transactions.choices import (
    TransactionType,
    BudgetPeriod,
    RecurrenceFrequency,
    NotificationType,
)
from transactions.models import (
    Category,
    Transaction,
    Budget,
    FinancialGoal,
    RecurringTransaction,
    Notification,
)
from transactions.services import NotificationService

User = get_user_model()


class NotificationModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notifuser1',
            email='notifuser1@example.com',
            password='Password123!'
        )

    def test_notification_creation_and_defaults(self):
        notif = Notification.objects.create(
            user=self.user,
            notification_type=NotificationType.BUDGET_WARNING,
            title='Budget Warning Test',
            message='You reached 80% of budget.',
            metadata={'budget_id': 1}
        )
        self.assertEqual(notif.user, self.user)
        self.assertEqual(notif.notification_type, NotificationType.BUDGET_WARNING)
        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)
        self.assertEqual(notif.metadata, {'budget_id': 1})
        self.assertIn('Budget Warning Test', str(notif))

    def test_mark_as_read_and_unread_methods(self):
        notif = Notification.objects.create(
            user=self.user,
            notification_type=NotificationType.GOAL_COMPLETED,
            title='Goal Done',
            message='Target reached.'
        )
        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)

        notif.mark_as_read()
        self.assertTrue(notif.is_read)
        self.assertIsNotNone(notif.read_at)

        notif.mark_as_unread()
        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)


class NotificationServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='serviceuser',
            email='serviceuser@example.com',
            password='Password123!'
        )
        self.category = Category.objects.create(user=self.user, name='Groceries')

    def test_create_budget_warning_and_exceeded_alerts(self):
        today = datetime.date.today()
        start = today.replace(day=1)
        end = today

        budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            name='Monthly Groceries',
            amount=Decimal('100.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=start,
            end_date=end
        )

        # 1. 50% spent - no alert
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('50.00'),
            date=today,
            description='Partial groceries'
        )
        notif1 = NotificationService.create_budget_alert(budget)
        self.assertIsNone(notif1)

        # 2. Spend another 35% -> Total 85% -> Warning alert generated
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('35.00'),
            date=today,
            description='More groceries'
        )
        notif2 = NotificationService.create_budget_alert(budget)
        self.assertIsNotNone(notif2)
        self.assertEqual(notif2.notification_type, NotificationType.BUDGET_WARNING)

        # Duplicate check - calling again produces None
        notif2_dup = NotificationService.create_budget_alert(budget)
        self.assertIsNone(notif2_dup)

        # 3. Spend another 25% -> Total 110% -> Exceeded alert generated
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('25.00'),
            date=today,
            description='Exceeding groceries'
        )
        notif3 = NotificationService.create_budget_alert(budget)
        self.assertIsNotNone(notif3)
        self.assertEqual(notif3.notification_type, NotificationType.BUDGET_EXCEEDED)

        # Duplicate check for exceeded
        notif3_dup = NotificationService.create_budget_alert(budget)
        self.assertIsNone(notif3_dup)

    def test_create_goal_warning_and_completed_alerts(self):
        target_dt = datetime.date.today() + datetime.timedelta(days=30)
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='Car Fund',
            target_amount=Decimal('1000.00'),
            target_date=target_dt,
            is_active=True
        )

        # 850 saved -> 85% -> Goal Warning
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('850.00'),
            date=datetime.date.today()
        )
        notif1 = NotificationService.create_goal_alert(goal)
        self.assertIsNotNone(notif1)
        self.assertEqual(notif1.notification_type, NotificationType.GOAL_WARNING)

        # Duplicate goal warning
        self.assertIsNone(NotificationService.create_goal_alert(goal))

        # Save remaining -> 100% -> Goal Completed
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('200.00'),
            date=datetime.date.today()
        )
        notif2 = NotificationService.create_goal_alert(goal)
        self.assertIsNotNone(notif2)
        self.assertEqual(notif2.notification_type, NotificationType.GOAL_COMPLETED)

        # Duplicate goal completed
        self.assertIsNone(NotificationService.create_goal_alert(goal))

    def test_create_recurring_alerts(self):
        today = datetime.date.today()
        schedule = RecurringTransaction.objects.create(
            user=self.user,
            category=self.category,
            name='Gym Membership',
            amount=Decimal('50.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=today,
            next_run_date=today,
            is_active=True
        )

        # 1. Due Alert
        due_notif = NotificationService.create_recurring_alert(schedule, NotificationType.RECURRING_DUE)
        self.assertIsNotNone(due_notif)
        self.assertEqual(due_notif.notification_type, NotificationType.RECURRING_DUE)

        # Duplicate Due Alert
        self.assertIsNone(NotificationService.create_recurring_alert(schedule, NotificationType.RECURRING_DUE))

        # Paused schedule skips due alert
        schedule.is_active = False
        schedule.save()
        schedule.next_run_date = today + datetime.timedelta(days=30)
        self.assertIsNone(NotificationService.create_recurring_alert(schedule, NotificationType.RECURRING_DUE))

    def test_mark_all_as_read(self):
        Notification.objects.create(user=self.user, notification_type=NotificationType.BUDGET_WARNING, title='N1', message='M1')
        Notification.objects.create(user=self.user, notification_type=NotificationType.GOAL_WARNING, title='N2', message='M2')

        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 2)

        updated_count = NotificationService.mark_all_as_read(self.user)
        self.assertEqual(updated_count, 2)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='Password123!')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='Password123!')

        self.n1 = Notification.objects.create(
            user=self.user1,
            notification_type=NotificationType.BUDGET_EXCEEDED,
            title='Budget Over Limit',
            message='You went over budget.',
            is_read=False
        )
        self.n2 = Notification.objects.create(
            user=self.user1,
            notification_type=NotificationType.GOAL_COMPLETED,
            title='Goal Reached',
            message='Target reached successfully.',
            is_read=True,
            read_at=datetime.datetime.now(datetime.timezone.utc)
        )
        self.n3_other = Notification.objects.create(
            user=self.user2,
            notification_type=NotificationType.RECURRING_DUE,
            title='User2 Bill',
            message='User2 bill due.',
            is_read=False
        )

        self.list_url = reverse('transactions:notification-list')
        self.mark_all_url = reverse('transactions:notification-mark-all-read')

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_user_notifications_isolation(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results), 2)
        titles = [n['title'] for n in results]
        self.assertIn('Budget Over Limit', titles)
        self.assertIn('Goal Reached', titles)
        self.assertNotIn('User2 Bill', titles)

    def test_retrieve_notification_success(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:notification-detail', kwargs={'pk': self.n1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Budget Over Limit')

    def test_retrieve_other_user_notification_returns_404(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:notification-detail', kwargs={'pk': self.n3_other.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_notification_mark_read_and_unread(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:notification-detail', kwargs={'pk': self.n1.pk})

        # Mark Read
        response = self.client.patch(url, {'is_read': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])
        self.assertIsNotNone(response.data['read_at'])

        # Mark Unread
        response = self.client.patch(url, {'is_read': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_read'])
        self.assertIsNone(response.data['read_at'])

    def test_patch_other_user_notification_returns_404(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:notification-detail', kwargs={'pk': self.n3_other.pk})
        response = self.client.patch(url, {'is_read': True})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_notification_success(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:notification-detail', kwargs={'pk': self.n1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notification.objects.filter(pk=self.n1.pk).exists())

    def test_delete_other_user_notification_returns_404(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:notification-detail', kwargs={'pk': self.n3_other.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_mark_all_read(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.mark_all_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_count'], 1)
        self.n1.refresh_from_db()
        self.assertTrue(self.n1.is_read)

    def test_filtering_and_search(self):
        self.client.force_authenticate(user=self.user1)

        # Filter by is_read=false
        res1 = self.client.get(f"{self.list_url}?is_read=false")
        self.assertEqual(len(res1.data['results']), 1)
        self.assertEqual(res1.data['results'][0]['id'], self.n1.id)

        # Filter by notification_type
        res2 = self.client.get(f"{self.list_url}?notification_type=GOAL_COMPLETED")
        self.assertEqual(len(res2.data['results']), 1)
        self.assertEqual(res2.data['results'][0]['id'], self.n2.id)

        # Search by keyword
        res3 = self.client.get(f"{self.list_url}?search=budget")
        self.assertEqual(len(res3.data['results']), 1)
        self.assertEqual(res3.data['results'][0]['id'], self.n1.id)

    def test_invalid_filter_params_raise_validation_error(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"{self.list_url}?notification_type=INVALID_TYPE")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('notification_type', response.data)


class NotificationManagementCommandTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cmduser', email='cmduser@example.com', password='Password123!')
        self.category = Category.objects.create(user=self.user, name='Utilities')

        today = datetime.date.today()
        # Create budget exceeding
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            name='Electricity',
            amount=Decimal('100.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=today.replace(day=1),
            end_date=today
        )
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('150.00'),
            date=today
        )

    def test_process_financial_notifications_command(self):
        call_command('process_financial_notifications')
        self.assertTrue(Notification.objects.filter(user=self.user, notification_type=NotificationType.BUDGET_EXCEEDED).exists())
