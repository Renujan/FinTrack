from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from transactions.choices import TransactionType
from transactions.models import Category, Transaction

User = get_user_model()


class ComprehensiveDay3ValidationTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(email='usera@example.com', password='Password123!', username='usera')
        self.user_b = User.objects.create_user(email='userb@example.com', password='Password123!', username='userb')

        self.cat_a1 = Category.objects.create(user=self.user_a, name='Entertainment')
        self.cat_b1 = Category.objects.create(user=self.user_b, name='Entertainment')

        self.cat_url = reverse('transactions:category-list-create')
        self.txn_url = reverse('transactions:transaction-list-create')

    # --- Category Tests ---
    def test_create_category(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.cat_url, {'name': 'Travel'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(user=self.user_a, name='Travel').exists())

    def test_duplicate_category_prevention(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.cat_url, {'name': 'Entertainment'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_category_name_allowed_for_different_users(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.cat_url, {'name': 'Utilities'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.user_b)
        response_b = self.client.post(self.cat_url, {'name': 'Utilities'})
        self.assertEqual(response_b.status_code, status.HTTP_201_CREATED)

    # --- Transaction Tests ---
    def test_create_income_transaction(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            'category': self.cat_a1.id,
            'transaction_type': TransactionType.INCOME,
            'amount': '1500.00',
            'description': 'Consulting work',
            'date': '2026-08-01'
        }
        response = self.client.post(self.txn_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['transaction_type'], TransactionType.INCOME)

    def test_create_expense_transaction(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            'category': self.cat_a1.id,
            'transaction_type': TransactionType.EXPENSE,
            'amount': '45.00',
            'description': 'Movie ticket',
            'date': '2026-08-02'
        }
        response = self.client.post(self.txn_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['transaction_type'], TransactionType.EXPENSE)

    def test_invalid_amount_rejection(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            'category': self.cat_a1.id,
            'transaction_type': TransactionType.EXPENSE,
            'amount': '0.00',
            'date': '2026-08-01'
        }
        response = self.client.post(self.txn_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_transaction_type_rejection(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            'category': self.cat_a1.id,
            'transaction_type': 'INVALID_TYPE',
            'amount': '100.00',
            'date': '2026-08-01'
        }
        response = self.client.post(self.txn_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cross_user_category_usage_rejection(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            'category': self.cat_b1.id,  # Owned by user_b
            'transaction_type': TransactionType.EXPENSE,
            'amount': '100.00',
            'date': '2026-08-01'
        }
        response = self.client.post(self.txn_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
