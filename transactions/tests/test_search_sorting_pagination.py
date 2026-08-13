from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from transactions.choices import TransactionType
from transactions.models import Category, Transaction

User = get_user_model()


class SearchSortingPaginationValidationTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='search1@example.com', password='Password123!', username='search1')
        self.user2 = User.objects.create_user(email='search2@example.com', password='Password123!', username='search2')

        self.cat_food = Category.objects.create(user=self.user1, name='Food')
        self.cat_salary = Category.objects.create(user=self.user1, name='Salary')
        self.cat_bills = Category.objects.create(user=self.user1, name='Bills')
        self.cat_user2 = Category.objects.create(user=self.user2, name='Food')

        self.t1 = Transaction.objects.create(
            user=self.user1,
            category=self.cat_food,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('25.50'),
            description='Lunch with team',
            date='2026-08-01'
        )
        self.t2 = Transaction.objects.create(
            user=self.user1,
            category=self.cat_salary,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('3000.00'),
            description='Monthly salary deposit',
            date='2026-08-05'
        )
        self.t3 = Transaction.objects.create(
            user=self.user1,
            category=self.cat_food,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('150.00'),
            description='Weekly grocery shopping',
            date='2026-08-10'
        )
        self.t4 = Transaction.objects.create(
            user=self.user1,
            category=self.cat_bills,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('80.00'),
            description='Electricity bill payment',
            date='2026-08-15'
        )
        self.t_user2 = Transaction.objects.create(
            user=self.user2,
            category=self.cat_user2,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('25.50'),
            description='Lunch with team',
            date='2026-08-01'
        )

        self.url = reverse('transactions:transaction-list-create')
        self.client.force_authenticate(user=self.user1)

    # --- Search Tests ---
    def test_search_by_description(self):
        response = self.client.get(f"{self.url}?search=grocery")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.t3.id)

    def test_search_by_category_name(self):
        response = self.client.get(f"{self.url}?search=Salary")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.t2.id)

    def test_search_case_insensitive(self):
        response = self.client.get(f"{self.url}?search=LUNCH")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.t1.id)

    def test_search_no_results(self):
        response = self.client.get(f"{self.url}?search=nonexistent")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_search_cross_user_isolation(self):
        response = self.client.get(f"{self.url}?search=Lunch")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for r in response.data['results']:
            self.assertNotEqual(r['id'], self.t_user2.id)

    # --- Filter Tests ---
    def test_filter_by_type(self):
        response = self.client.get(f"{self.url}?type=income")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.t2.id)

    def test_filter_by_category_name_and_id(self):
        response_name = self.client.get(f"{self.url}?category=Food")
        self.assertEqual(response_name.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_name.data['results']), 2)

        response_id = self.client.get(f"{self.url}?category={self.cat_bills.id}")
        self.assertEqual(response_id.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_id.data['results']), 1)
        self.assertEqual(response_id.data['results'][0]['id'], self.t4.id)

    def test_filter_by_min_and_max_amount(self):
        response = self.client.get(f"{self.url}?min_amount=50&max_amount=200")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        ids = [r['id'] for r in results]
        self.assertIn(self.t3.id, ids)
        self.assertIn(self.t4.id, ids)

    def test_combined_filters(self):
        response = self.client.get(
            f"{self.url}?type=expense&category=Food&min_amount=100&start_date=2026-08-01&end_date=2026-08-31"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.t3.id)

    # --- Sorting Tests ---
    def test_sorting_amount_ascending(self):
        response = self.client.get(f"{self.url}?ordering=amount")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        amounts = [Decimal(str(r['amount'])) for r in response.data['results']]
        self.assertEqual(amounts, sorted(amounts))

    def test_sorting_amount_descending(self):
        response = self.client.get(f"{self.url}?ordering=-amount")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        amounts = [Decimal(str(r['amount'])) for r in response.data['results']]
        self.assertEqual(amounts, sorted(amounts, reverse=True))

    def test_sorting_transaction_date_alias(self):
        response = self.client.get(f"{self.url}?ordering=transaction_date")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dates = [r['date'] for r in response.data['results']]
        self.assertEqual(dates, sorted(dates))

    def test_sorting_invalid_field_rejection(self):
        response = self.client.get(f"{self.url}?ordering=invalid_field")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ordering', response.data)

    # --- Filter Validation Tests ---
    def test_invalid_date_format_fails(self):
        response = self.client.get(f"{self.url}?start_date=not-a-date")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date', response.data)

    def test_invalid_date_range_fails(self):
        response = self.client.get(f"{self.url}?start_date=2026-08-31&end_date=2026-08-01")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date', response.data)

    def test_invalid_amount_format_fails(self):
        response = self.client.get(f"{self.url}?min_amount=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('min_amount', response.data)

    def test_invalid_amount_range_fails(self):
        response = self.client.get(f"{self.url}?min_amount=1000&max_amount=100")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('min_amount', response.data)

    def test_invalid_type_fails(self):
        response = self.client.get(f"{self.url}?type=unsupported_type")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('type', response.data)

    # --- Pagination Tests ---
    def test_pagination_page_size(self):
        response = self.client.get(f"{self.url}?page_size=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['next'])

    def test_pagination_and_search_combination(self):
        response = self.client.get(f"{self.url}?search=Lunch&page=1&page_size=10")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
