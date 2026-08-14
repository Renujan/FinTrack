from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from transactions.choices import TransactionType
from transactions.models import Category, Transaction

User = get_user_model()


class Day5APIIntegrationTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='day5user1',
            email='day5user1@example.com',
            password='SecurePassword123!',
            currency='USD'
        )
        self.user2 = User.objects.create_user(
            username='day5user2',
            email='day5user2@example.com',
            password='SecurePassword123!',
            currency='EUR'
        )

        self.cat1 = Category.objects.create(user=self.user1, name='Groceries')
        self.cat2 = Category.objects.create(user=self.user1, name='Rent')
        self.cat3 = Category.objects.create(user=self.user2, name='Utilities')

        self.txn1 = Transaction.objects.create(
            user=self.user1,
            category=self.cat1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('150.00'),
            description='Supermarket grocery shopping',
            date='2026-08-10'
        )
        self.txn2 = Transaction.objects.create(
            user=self.user1,
            category=self.cat2,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('1200.00'),
            description='Monthly apartment rent payment',
            date='2026-08-11'
        )
        self.txn3 = Transaction.objects.create(
            user=self.user1,
            category=self.cat1,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('500.00'),
            description='Freelance bonus reimbursement',
            date='2026-08-12'
        )

        self.cat_list_url = reverse('transactions:category-list-create')
        self.cat_detail_url_1 = reverse('transactions:category-detail', kwargs={'pk': self.cat1.pk})
        self.cat_detail_url_3 = reverse('transactions:category-detail', kwargs={'pk': self.cat3.pk})
        self.txn_list_url = reverse('transactions:transaction-list-create')
        self.txn_detail_url_1 = reverse('transactions:transaction-detail', kwargs={'pk': self.txn1.pk})

    # --- 1. Category Search & Pagination Tests ---
    def test_category_search_by_name(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.cat_list_url, {'search': 'Groc'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Groceries')

    def test_category_pagination(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.cat_list_url, {'page_size': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 1)

    # --- 2. API Validation Edge Cases ---
    def test_transaction_create_negative_amount_fails(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            'category': self.cat1.id,
            'transaction_type': 'EXPENSE',
            'amount': '-50.00',
            'date': '2026-08-12'
        }
        response = self.client.post(self.txn_list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_transaction_create_zero_amount_fails(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            'category': self.cat1.id,
            'transaction_type': 'EXPENSE',
            'amount': '0.00',
            'date': '2026-08-12'
        }
        response = self.client.post(self.txn_list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_transaction_create_other_user_category_fails(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            'category': self.cat3.id, # belongs to user2
            'transaction_type': 'EXPENSE',
            'amount': '50.00',
            'date': '2026-08-12'
        }
        response = self.client.post(self.txn_list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- 3. Filtering & Search Combo Tests ---
    def test_transaction_filtering_by_type_and_search(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.txn_list_url, {
            'type': 'expense',
            'search': 'Supermarket'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.txn1.id)

    def test_transaction_filtering_by_amount_range(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.txn_list_url, {
            'min_amount': '200.00',
            'max_amount': '1500.00'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)

    def test_invalid_filter_params_returns_400(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.txn_list_url, {'start_date': 'invalid-date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date', response.data)

    # --- 4. Permissions & Auth Error Handling ---
    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(self.txn_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_user_transaction_access_returns_404(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.txn_detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cross_user_category_access_returns_404(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.cat_detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
