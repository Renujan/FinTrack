from decimal import Decimal
import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from transactions.choices import BudgetPeriod, TransactionType
from transactions.models import Category, Transaction, Budget
from transactions.services import BudgetCalculationService

User = get_user_model()


class BudgetModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='Password123!')
        self.category = Category.objects.create(user=self.user, name='Groceries')

    def test_budget_creation_category(self):
        budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            name='Monthly Groceries',
            amount=Decimal('500.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 31)
        )
        self.assertEqual(budget.name, 'Monthly Groceries')
        self.assertEqual(budget.amount, Decimal('500.00'))
        self.assertFalse(budget.is_overall)
        self.assertEqual(str(budget), f"Monthly Groceries - 500.00 ({self.user})")

    def test_budget_creation_overall(self):
        budget = Budget.objects.create(
            user=self.user,
            category=None,
            name='Overall Monthly Budget',
            amount=Decimal('1000.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 31)
        )
        self.assertTrue(budget.is_overall)
        self.assertIsNone(budget.category)


class BudgetCalculationServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='calcuser', email='calc@example.com', password='Password123!')
        self.category1 = Category.objects.create(user=self.user, name='Food')
        self.category2 = Category.objects.create(user=self.user, name='Utilities')

        self.budget_cat = Budget.objects.create(
            user=self.user,
            category=self.category1,
            name='Food Budget',
            amount=Decimal('500.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 31)
        )

        self.budget_overall = Budget.objects.create(
            user=self.user,
            category=None,
            name='Overall Budget',
            amount=Decimal('1000.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 31)
        )

    def test_no_spending(self):
        metrics = BudgetCalculationService.calculate_budget_metrics(self.budget_cat)
        self.assertEqual(metrics['spent_amount'], Decimal('0.00'))
        self.assertEqual(metrics['remaining_amount'], Decimal('500.00'))
        self.assertEqual(metrics['percentage_used'], 0.0)
        self.assertFalse(metrics['is_exceeded'])

    def test_partial_spending(self):
        Transaction.objects.create(
            user=self.user,
            category=self.category1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('150.00'),
            date=datetime.date(2026, 8, 10)
        )
        Transaction.objects.create(
            user=self.user,
            category=self.category1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('200.00'),
            date=datetime.date(2026, 8, 15)
        )

        metrics = BudgetCalculationService.calculate_budget_metrics(self.budget_cat)
        self.assertEqual(metrics['spent_amount'], Decimal('350.00'))
        self.assertEqual(metrics['remaining_amount'], Decimal('150.00'))
        self.assertEqual(metrics['percentage_used'], 70.0)
        self.assertFalse(metrics['is_exceeded'])

    def test_exceeded_budget(self):
        Transaction.objects.create(
            user=self.user,
            category=self.category1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('600.00'),
            date=datetime.date(2026, 8, 10)
        )

        metrics = BudgetCalculationService.calculate_budget_metrics(self.budget_cat)
        self.assertEqual(metrics['spent_amount'], Decimal('600.00'))
        self.assertEqual(metrics['remaining_amount'], Decimal('-100.00'))
        self.assertEqual(metrics['percentage_used'], 120.0)
        self.assertTrue(metrics['is_exceeded'])

    def test_income_excluded_from_spending(self):
        Transaction.objects.create(
            user=self.user,
            category=self.category1,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('1000.00'),
            date=datetime.date(2026, 8, 10)
        )
        Transaction.objects.create(
            user=self.user,
            category=self.category1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('100.00'),
            date=datetime.date(2026, 8, 12)
        )

        metrics = BudgetCalculationService.calculate_budget_metrics(self.budget_cat)
        self.assertEqual(metrics['spent_amount'], Decimal('100.00'))
        self.assertEqual(metrics['remaining_amount'], Decimal('400.00'))

    def test_dates_outside_range_excluded(self):
        # Expense before budget period
        Transaction.objects.create(
            user=self.user,
            category=self.category1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('100.00'),
            date=datetime.date(2026, 7, 31)
        )
        # Expense after budget period
        Transaction.objects.create(
            user=self.user,
            category=self.category1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('100.00'),
            date=datetime.date(2026, 9, 1)
        )
        # Expense inside budget period
        Transaction.objects.create(
            user=self.user,
            category=self.category1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('50.00'),
            date=datetime.date(2026, 8, 5)
        )

        metrics = BudgetCalculationService.calculate_budget_metrics(self.budget_cat)
        self.assertEqual(metrics['spent_amount'], Decimal('50.00'))

    def test_overall_budget_includes_all_user_expenses(self):
        Transaction.objects.create(
            user=self.user,
            category=self.category1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('200.00'),
            date=datetime.date(2026, 8, 10)
        )
        Transaction.objects.create(
            user=self.user,
            category=self.category2,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('300.00'),
            date=datetime.date(2026, 8, 20)
        )

        metrics_overall = BudgetCalculationService.calculate_budget_metrics(self.budget_overall)
        self.assertEqual(metrics_overall['spent_amount'], Decimal('500.00'))
        self.assertEqual(metrics_overall['remaining_amount'], Decimal('500.00'))


class BudgetAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='Password123!')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='Password123!')

        self.category1 = Category.objects.create(user=self.user1, name='Dining Out')
        self.category2 = Category.objects.create(user=self.user2, name='Shopping')

        self.url_list = reverse('transactions:budget-list-create')

        self.budget1 = Budget.objects.create(
            user=self.user1,
            category=self.category1,
            name='Dining Budget',
            amount=Decimal('300.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 31)
        )

    def test_unauthenticated_request_denied(self):
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_category_budget_success(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            'name': 'Monthly Dining',
            'category': self.category1.id,
            'amount': '250.00',
            'period': 'MONTHLY',
            'start_date': '2026-08-01',
            'end_date': '2026-08-31'
        }
        response = self.client.post(self.url_list, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Monthly Dining')
        self.assertEqual(response.data['category'], self.category1.id)
        self.assertEqual(response.data['category_name'], 'Dining Out')
        self.assertFalse(response.data['is_overall'])
        self.assertEqual(response.data['amount'], '250.00')

    def test_create_overall_budget_success(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            'name': 'Overall August',
            'category': None,
            'amount': '1000.00',
            'period': 'MONTHLY',
            'start_date': '2026-08-01',
            'end_date': '2026-08-31'
        }
        response = self.client.post(self.url_list, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_overall'])
        self.assertIsNone(response.data['category'])

    def test_create_budget_using_other_user_category_fails(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            'name': 'Hacked Budget',
            'category': self.category2.id,
            'amount': '100.00',
            'period': 'MONTHLY',
            'start_date': '2026-08-01',
            'end_date': '2026-08-31'
        }
        response = self.client.post(self.url_list, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_budget_invalid_amount_fails(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            'name': 'Zero Budget',
            'amount': '0.00',
            'period': 'MONTHLY',
            'start_date': '2026-08-01',
            'end_date': '2026-08-31'
        }
        response = self.client.post(self.url_list, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_budget_end_date_before_start_date_fails(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            'name': 'Invalid Date Budget',
            'amount': '100.00',
            'period': 'CUSTOM',
            'start_date': '2026-08-31',
            'end_date': '2026-08-01'
        }
        response = self.client.post(self.url_list, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_budget_invalid_period_fails(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            'name': 'Invalid Period Budget',
            'amount': '100.00',
            'period': 'YEARLY',
            'start_date': '2026-08-01',
            'end_date': '2026-08-31'
        }
        response = self.client.post(self.url_list, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_list_user_budgets_only(self):
        # Create budget for user2
        Budget.objects.create(
            user=self.user2,
            name='User 2 Budget',
            amount=Decimal('400.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 31)
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.budget1.id)

    def test_retrieve_budget_detail(self):
        self.client.force_authenticate(user=self.user1)
        url_detail = reverse('transactions:budget-detail', kwargs={'pk': self.budget1.id})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.budget1.name)
        self.assertIn('spent_amount', response.data)
        self.assertIn('remaining_amount', response.data)

    def test_update_budget(self):
        self.client.force_authenticate(user=self.user1)
        url_detail = reverse('transactions:budget-detail', kwargs={'pk': self.budget1.id})
        payload = {'amount': '350.00'}
        response = self.client.patch(url_detail, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '350.00')

    def test_delete_budget(self):
        self.client.force_authenticate(user=self.user1)
        url_detail = reverse('transactions:budget-detail', kwargs={'pk': self.budget1.id})
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Budget.objects.filter(id=self.budget1.id).exists())

    def test_cross_user_access_returns_404(self):
        self.client.force_authenticate(user=self.user2)
        url_detail = reverse('transactions:budget-detail', kwargs={'pk': self.budget1.id})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response_patch = self.client.patch(url_detail, {'amount': '500.00'})
        self.assertEqual(response_patch.status_code, status.HTTP_404_NOT_FOUND)

        response_delete = self.client.delete(url_detail)
        self.assertEqual(response_delete.status_code, status.HTTP_404_NOT_FOUND)


class BudgetFilteringSearchPaginationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='filteruser', email='filter@example.com', password='Password123!')
        self.category_food = Category.objects.create(user=self.user, name='Food & Drinks')
        self.category_travel = Category.objects.create(user=self.user, name='Travel')

        self.b1 = Budget.objects.create(
            user=self.user,
            category=self.category_food,
            name='Weekly Food',
            amount=Decimal('100.00'),
            period=BudgetPeriod.WEEKLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 7)
        )
        self.b2 = Budget.objects.create(
            user=self.user,
            category=self.category_travel,
            name='Monthly Travel',
            amount=Decimal('500.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 31)
        )
        self.b3 = Budget.objects.create(
            user=self.user,
            category=None,
            name='Overall Summer',
            amount=Decimal('2000.00'),
            period=BudgetPeriod.CUSTOM,
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 8, 31)
        )

        # Add transaction that exceeds b1
        Transaction.objects.create(
            user=self.user,
            category=self.category_food,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('150.00'),
            date=datetime.date(2026, 8, 3)
        )

        self.url = reverse('transactions:budget-list-create')
        self.client.force_authenticate(user=self.user)

    def test_filter_by_category_name(self):
        response = self.client.get(self.url, {'category': 'Food & Drinks'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.b1.id)

    def test_filter_by_period(self):
        response = self.client.get(self.url, {'period': 'WEEKLY'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.b1.id)

    def test_filter_by_is_overall(self):
        response = self.client.get(self.url, {'is_overall': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.b3.id)

    def test_filter_by_is_exceeded(self):
        response = self.client.get(self.url, {'is_exceeded': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.b1.id)

    def test_search_by_budget_name(self):
        response = self.client.get(self.url, {'search': 'Travel'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Monthly Travel')

    def test_ordering_by_amount(self):
        response = self.client.get(self.url, {'ordering': 'amount'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        amounts = [float(item['amount']) for item in response.data['results']]
        self.assertEqual(amounts, sorted(amounts))

    def test_ordering_by_percentage_used(self):
        response = self.client.get(self.url, {'ordering': '-percentage_used'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        percentages = [item['percentage_used'] for item in response.data['results']]
        self.assertEqual(percentages[0], 150.0)

    def test_budget_pagination(self):
        response = self.client.get(self.url, {'page_size': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['count'], 3)
        self.assertIsNotNone(response.data['next'])
