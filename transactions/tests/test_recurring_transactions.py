import datetime
from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from transactions.choices import RecurrenceFrequency, TransactionType, BudgetPeriod
from transactions.models import Category, Transaction, Budget, RecurringTransaction
from transactions.services import RecurringTransactionService, BudgetCalculationService
from users.models import User


@pytest.mark.django_db
class TestRecurringTransactionModel:

    def test_recurring_transaction_creation(self, db):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='Password123!')
        category = Category.objects.create(user=user, name='Utilities')
        recurring = RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Electricity Bill',
            amount=Decimal('150.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1)
        )
        assert recurring.id is not None
        assert str(recurring) == f"Electricity Bill - MONTHLY - 150.00 ({user})"
        assert recurring.is_active is True
        assert recurring.last_run_date is None

    def test_recurring_transaction_choices_validation(self):
        assert RecurrenceFrequency.is_valid_frequency('DAILY') is True
        assert RecurrenceFrequency.is_valid_frequency('WEEKLY') is True
        assert RecurrenceFrequency.is_valid_frequency('MONTHLY') is True
        assert RecurrenceFrequency.is_valid_frequency('YEARLY') is True
        assert RecurrenceFrequency.is_valid_frequency('HOURLY') is False


@pytest.mark.django_db
class TestNextOccurrenceCalculations:

    def test_daily_next_run(self):
        start = datetime.date(2026, 1, 15)
        nxt = RecurringTransactionService.calculate_next_run_date(start, RecurrenceFrequency.DAILY)
        assert nxt == datetime.date(2026, 1, 16)

    def test_weekly_next_run(self):
        start = datetime.date(2026, 1, 15)
        nxt = RecurringTransactionService.calculate_next_run_date(start, RecurrenceFrequency.WEEKLY)
        assert nxt == datetime.date(2026, 1, 22)

    def test_monthly_next_run_standard(self):
        start = datetime.date(2026, 1, 15)
        nxt = RecurringTransactionService.calculate_next_run_date(start, RecurrenceFrequency.MONTHLY)
        assert nxt == datetime.date(2026, 2, 15)

    def test_monthly_next_run_month_end(self):
        # Jan 31 -> Feb 28 in non-leap year
        start = datetime.date(2026, 1, 31)
        nxt = RecurringTransactionService.calculate_next_run_date(start, RecurrenceFrequency.MONTHLY)
        assert nxt == datetime.date(2026, 2, 28)

    def test_yearly_next_run_leap_year(self):
        # Feb 29, 2024 -> Feb 28, 2025
        start = datetime.date(2024, 2, 29)
        nxt = RecurringTransactionService.calculate_next_run_date(start, RecurrenceFrequency.YEARLY)
        assert nxt == datetime.date(2025, 2, 28)


@pytest.mark.django_db
class TestRecurringTransactionAPI:

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username='apiuser', email='apiuser@example.com', password='Password123!')

    @pytest.fixture
    def other_user(self, db):
        return User.objects.create_user(username='otheruser', email='otheruser@example.com', password='Password123!')

    @pytest.fixture
    def category(self, user):
        return Category.objects.create(user=user, name='Rent & Housing')

    @pytest.fixture
    def other_category(self, other_user):
        return Category.objects.create(user=other_user, name='Other Category')

    def test_unauthenticated_access_denied(self, api_client):
        url = reverse('transactions:recurring-transaction-list-create')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_recurring_transaction(self, api_client, user, category):
        api_client.force_authenticate(user=user)
        url = reverse('transactions:recurring-transaction-list-create')
        payload = {
            'name': 'Monthly Apartment Rent',
            'category': category.id,
            'amount': '1200.00',
            'transaction_type': 'EXPENSE',
            'frequency': 'MONTHLY',
            'start_date': '2026-01-01',
            'description': 'Main rent payment'
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Monthly Apartment Rent'
        assert response.data['next_run_date'] == '2026-01-01'

    def test_create_recurring_transaction_invalid_category(self, api_client, user, other_category):
        api_client.force_authenticate(user=user)
        url = reverse('transactions:recurring-transaction-list-create')
        payload = {
            'name': 'Invalid Category Rent',
            'category': other_category.id,
            'amount': '1200.00',
            'transaction_type': 'EXPENSE',
            'frequency': 'MONTHLY',
            'start_date': '2026-01-01'
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_recurring_transaction_invalid_date_range(self, api_client, user, category):
        api_client.force_authenticate(user=user)
        url = reverse('transactions:recurring-transaction-list-create')
        payload = {
            'name': 'Bad Dates',
            'category': category.id,
            'amount': '50.00',
            'transaction_type': 'EXPENSE',
            'frequency': 'WEEKLY',
            'start_date': '2026-05-01',
            'end_date': '2026-04-01'
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_and_update_recurring_transaction(self, api_client, user, category):
        api_client.force_authenticate(user=user)
        rec = RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Gym Membership',
            amount=Decimal('45.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1)
        )
        url = reverse('transactions:recurring-transaction-detail', kwargs={'pk': rec.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['amount'] == '45.00'

        patch_payload = {'amount': '55.00'}
        patch_res = api_client.patch(url, patch_payload, format='json')
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.data['amount'] == '55.00'

    def test_cross_user_access_prevented(self, api_client, user, other_user, other_category):
        rec = RecurringTransaction.objects.create(
            user=other_user,
            category=other_category,
            name='Secret Recurring',
            amount=Decimal('100.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1)
        )
        api_client.force_authenticate(user=user)
        url = reverse('transactions:recurring-transaction-detail', kwargs={'pk': rec.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pause_and_resume_endpoints(self, api_client, user, category):
        api_client.force_authenticate(user=user)
        rec = RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Netflix Subscription',
            amount=Decimal('15.99'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1),
            is_active=True
        )

        pause_url = reverse('transactions:recurring-transaction-pause', kwargs={'pk': rec.id})
        pause_res = api_client.post(pause_url)
        assert pause_res.status_code == status.HTTP_200_OK
        assert pause_res.data['is_active'] is False

        rec.refresh_from_db()
        assert rec.is_active is False

        resume_url = reverse('transactions:recurring-transaction-resume', kwargs={'pk': rec.id})
        resume_res = api_client.post(resume_url)
        assert resume_res.status_code == status.HTTP_200_OK
        assert resume_res.data['is_active'] is True

        rec.refresh_from_db()
        assert rec.is_active is True

    def test_delete_recurring_transaction(self, api_client, user, category):
        api_client.force_authenticate(user=user)
        rec = RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Temporary Subscription',
            amount=Decimal('10.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1)
        )
        url = reverse('transactions:recurring-transaction-detail', kwargs={'pk': rec.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not RecurringTransaction.objects.filter(id=rec.id).exists()


@pytest.mark.django_db
class TestGenerationServiceAndDuplicateProtection:

    def test_generation_service_processes_due_transactions(self, db):
        user = User.objects.create_user(username='genuser', email='gen@example.com', password='Password123!')
        category = Category.objects.create(user=user, name='Salary')

        rec = RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Monthly Salary Income',
            amount=Decimal('5000.00'),
            transaction_type=TransactionType.INCOME,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1)
        )

        res = RecurringTransactionService.process_due_recurring_transactions(target_date=datetime.date(2026, 1, 1))
        assert res['generated_transactions_count'] == 1
        assert Transaction.objects.filter(user=user).count() == 1

        tx = Transaction.objects.get(user=user)
        assert tx.amount == Decimal('5000.00')
        assert tx.transaction_type == TransactionType.INCOME
        assert tx.date == datetime.date(2026, 1, 1)

        rec.refresh_from_db()
        assert rec.last_run_date == datetime.date(2026, 1, 1)
        assert rec.next_run_date == datetime.date(2026, 2, 1)

    def test_duplicate_generation_prevention(self, db):
        user = User.objects.create_user(username='dupuser', email='dup@example.com', password='Password123!')
        category = Category.objects.create(user=user, name='Subscriptions')

        rec = RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Software License',
            amount=Decimal('99.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1)
        )

        # First run
        res1 = RecurringTransactionService.process_due_recurring_transactions(target_date=datetime.date(2026, 1, 1))
        assert res1['generated_transactions_count'] == 1

        # Second run on same target_date
        res2 = RecurringTransactionService.process_due_recurring_transactions(target_date=datetime.date(2026, 1, 1))
        assert res2['generated_transactions_count'] == 0
        assert Transaction.objects.filter(user=user).count() == 1

    def test_paused_and_expired_schedules_skipped(self, db):
        user = User.objects.create_user(username='skipuser', email='skip@example.com', password='Password123!')
        category = Category.objects.create(user=user, name='Utilities')

        # Paused schedule
        rec_paused = RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Paused Water Bill',
            amount=Decimal('40.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1),
            is_active=False
        )

        # Expired schedule
        rec_expired = RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Expired Loan Payment',
            amount=Decimal('300.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 15),
            next_run_date=datetime.date(2026, 2, 1),
            is_active=True
        )

        res = RecurringTransactionService.process_due_recurring_transactions(target_date=datetime.date(2026, 2, 1))
        assert res['generated_transactions_count'] == 0

    def test_management_command_execution(self, db):
        from django.core.management import call_command
        user = User.objects.create_user(username='cmduser', email='cmd@example.com', password='Password123!')
        category = Category.objects.create(user=user, name='Internet')

        RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Fiber Broadband',
            amount=Decimal('60.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1)
        )

        call_command('process_recurring_transactions', date='2026-01-01')
        assert Transaction.objects.filter(user=user).count() == 1


@pytest.mark.django_db
class TestIntegrationWithBudgetsAndAnalytics:

    def test_generated_expense_affects_budget_metrics(self, db):
        user = User.objects.create_user(username='buser', email='buser@example.com', password='Password123!')
        category = Category.objects.create(user=user, name='Groceries')

        budget = Budget.objects.create(
            user=user,
            category=category,
            name='Monthly Groceries Budget',
            amount=Decimal('500.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 31)
        )

        rec = RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Weekly Grocery Order',
            amount=Decimal('150.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.WEEKLY,
            start_date=datetime.date(2026, 1, 7),
            next_run_date=datetime.date(2026, 1, 7)
        )

        # Process first week
        RecurringTransactionService.process_due_recurring_transactions(target_date=datetime.date(2026, 1, 7))

        metrics = BudgetCalculationService.calculate_budget_metrics(budget)
        assert metrics['spent_amount'] == Decimal('150.00')
        assert metrics['remaining_amount'] == Decimal('350.00')


@pytest.mark.django_db
class TestFilteringSearchingOrderingPagination:

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username='filteruser', email='filter@example.com', password='Password123!')

    @pytest.fixture
    def category(self, user):
        return Category.objects.create(user=user, name='Utilities')

    def test_filtering_and_ordering(self, api_client, user, category):
        api_client.force_authenticate(user=user)

        RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Water Bill',
            amount=Decimal('30.00'),
            transaction_type=TransactionType.EXPENSE,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1)
        )
        RecurringTransaction.objects.create(
            user=user,
            category=category,
            name='Consulting Retainer',
            amount=Decimal('2000.00'),
            transaction_type=TransactionType.INCOME,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 1, 1)
        )

        url = reverse('transactions:recurring-transaction-list-create')

        # Filter by type=INCOME
        res_income = api_client.get(f"{url}?type=INCOME")
        assert res_income.status_code == status.HTTP_200_OK
        assert len(res_income.data['results']) == 1
        assert res_income.data['results'][0]['name'] == 'Consulting Retainer'

        # Search by 'Water'
        res_search = api_client.get(f"{url}?search=Water")
        assert res_search.status_code == status.HTTP_200_OK
        assert len(res_search.data['results']) == 1

        # Ordering by amount descending
        res_order = api_client.get(f"{url}?ordering=-amount")
        assert res_order.status_code == status.HTTP_200_OK
        assert res_order.data['results'][0]['amount'] == '2000.00'
