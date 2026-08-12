from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from transactions.choices import TransactionType
from transactions.models import Category, Transaction

User = get_user_model()


class FilterAndPaginationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='filter@example.com', password='Password123!', username='filteruser')
        self.user_other = User.objects.create_user(email='other@example.com', password='Password123!', username='otheruser')

        self.cat_food = Category.objects.create(user=self.user, name='Food')
        self.cat_salary = Category.objects.create(user=self.user, name='Salary')
        self.cat_other_food = Category.objects.create(user=self.user_other, name='Food')

        self.t1 = Transaction.objects.create(
            user=self.user,
            category=self.cat_food,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('15.00'),
            date='2026-08-01'
        )
        self.t2 = Transaction.objects.create(
            user=self.user,
            category=self.cat_food,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('25.00'),
            date='2026-08-15'
        )
        self.t3 = Transaction.objects.create(
            user=self.user,
            category=self.cat_salary,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('2000.00'),
            date='2026-08-10'
        )

        self.t_other = Transaction.objects.create(
            user=self.user_other,
            category=self.cat_other_food,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('999.00'),
            date='2026-08-01'
        )

        self.url = reverse('transactions:transaction-list-create')
        self.client.force_authenticate(user=self.user)

    def test_filter_by_type_expense(self):
        response = self.client.get(f"{self.url}?type=EXPENSE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertEqual(r['transaction_type'], TransactionType.EXPENSE)

    def test_filter_by_type_income(self):
        response = self.client.get(f"{self.url}?type=income")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['transaction_type'], TransactionType.INCOME)

    def test_filter_by_category_name(self):
        response = self.client.get(f"{self.url}?category=Food")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)

    def test_filter_by_date_range(self):
        response = self.client.get(f"{self.url}?start_date=2026-08-05&end_date=2026-08-12")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.t3.id)

    def test_filter_never_bypasses_ownership(self):
        response = self.client.get(f"{self.url}?category=Food")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for r in response.data['results']:
            self.assertNotEqual(r['id'], self.t_other.id)

    def test_pagination_structure(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 3)
