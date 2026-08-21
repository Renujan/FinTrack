import io
from decimal import Decimal
import datetime
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from transactions.choices import TransactionType, BudgetPeriod, RecurrenceFrequency, GoalStatus
from transactions.models import Category, Transaction, Budget, FinancialGoal, RecurringTransaction

User = get_user_model()


class Day12ExportImportAndReportTests(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123')

        self.cat_groceries = Category.objects.create(user=self.user1, name='Groceries')
        self.cat_salary = Category.objects.create(user=self.user1, name='Salary')
        self.cat_user2 = Category.objects.create(user=self.user2, name='User2 Category')

        self.txn1 = Transaction.objects.create(
            user=self.user1,
            category=self.cat_salary,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('5000.00'),
            description='Monthly Salary',
            date=datetime.date(2026, 1, 15)
        )

        self.txn2 = Transaction.objects.create(
            user=self.user1,
            category=self.cat_groceries,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('150.50'),
            description='Supermarket shopping',
            date=datetime.date(2026, 1, 20)
        )

        self.txn_user2 = Transaction.objects.create(
            user=self.user2,
            category=self.cat_user2,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('3000.00'),
            description='User 2 Income',
            date=datetime.date(2026, 1, 10)
        )

        self.budget1 = Budget.objects.create(
            user=self.user1,
            category=self.cat_groceries,
            name='Groceries Budget',
            amount=Decimal('500.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 31)
        )

        self.goal1 = FinancialGoal.objects.create(
            user=self.user1,
            category=self.cat_salary,
            name='Emergency Fund',
            target_amount=Decimal('10000.00'),
            target_date=datetime.date(2026, 12, 31)
        )

        self.recurring1 = RecurringTransaction.objects.create(
            user=self.user1,
            category=self.cat_salary,
            name='Monthly Salary Schedule',
            amount=Decimal('5000.00'),
            transaction_type=TransactionType.INCOME,
            frequency=RecurrenceFrequency.MONTHLY,
            start_date=datetime.date(2026, 1, 1),
            next_run_date=datetime.date(2026, 2, 1)
        )

    # -------------------------------------------------------------------------
    # 1. TRANSACTION CSV EXPORT TESTS
    # -------------------------------------------------------------------------

    def test_export_transactions_csv_success(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:export-transactions')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="transactions_export.csv"', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        self.assertGreaterEqual(len(lines), 3)  # Header + 2 txns

        header = lines[0]
        self.assertIn('Date', header)
        self.assertIn('Description', header)
        self.assertIn('Amount', header)
        self.assertIn('Transaction Type', header)
        self.assertIn('Category', header)

        self.assertIn('Monthly Salary', content)
        self.assertIn('5000.00', content)
        self.assertIn('Supermarket shopping', content)
        self.assertIn('150.50', content)
        self.assertNotIn('User 2 Income', content)

    def test_export_transactions_csv_date_filtering(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:export-transactions')
        response = self.client.get(url, {'start_date': '2026-01-18', 'end_date': '2026-01-25'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        self.assertIn('Supermarket shopping', content)
        self.assertNotIn('Monthly Salary', content)

    def test_export_transactions_csv_category_filtering(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:export-transactions')
        response = self.client.get(url, {'category': 'Groceries'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        self.assertIn('Supermarket shopping', content)
        self.assertNotIn('Monthly Salary', content)

    def test_export_transactions_csv_type_filtering(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:export-transactions')
        response = self.client.get(url, {'type': 'EXPENSE'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        self.assertIn('Supermarket shopping', content)
        self.assertNotIn('Monthly Salary', content)

    def test_export_transactions_csv_search(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:export-transactions')
        response = self.client.get(url, {'search': 'Supermarket'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        self.assertIn('Supermarket shopping', content)
        self.assertNotIn('Monthly Salary', content)

    def test_export_transactions_empty(self):
        empty_user = User.objects.create_user(username='emptyuser', password='password123')
        self.client.force_authenticate(user=empty_user)
        url = reverse('transactions:export-transactions')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)  # Only header line

    # -------------------------------------------------------------------------
    # 2. OTHER FINANCIAL DATA EXPORTS
    # -------------------------------------------------------------------------

    def test_export_categories_csv(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:export-categories')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Groceries', content)
        self.assertIn('Salary', content)
        self.assertNotIn('User2 Category', content)

    def test_export_budgets_csv(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:export-budgets')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        self.assertIn('Groceries Budget', content)
        self.assertIn('500.00', content)

    def test_export_goals_csv(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:export-goals')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        self.assertIn('Emergency Fund', content)
        self.assertIn('10000.00', content)

    def test_export_recurring_csv(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:export-recurring')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        self.assertIn('Monthly Salary Schedule', content)
        self.assertIn('5000.00', content)

    # -------------------------------------------------------------------------
    # 3. FINANCIAL REPORT API TESTS
    # -------------------------------------------------------------------------

    def test_financial_report_success(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:reports-financial')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['total_income'], '5000.00')
        self.assertEqual(data['total_expenses'], '150.50')
        self.assertEqual(data['net_balance'], '4849.50')
        self.assertEqual(data['transaction_count'], 2)

        self.assertIn('top_spending_categories', data)
        self.assertIn('category_spending_breakdown', data)
        self.assertIn('monthly_totals', data)
        self.assertIn('budget_summary', data)
        self.assertIn('goal_summary', data)

        self.assertEqual(data['budget_summary']['total_budgets'], 1)
        self.assertEqual(data['goal_summary']['total_goals'], 1)

    def test_financial_report_date_filtering(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:reports-financial')
        response = self.client.get(url, {'start_date': '2026-01-01', 'end_date': '2026-01-31'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['transaction_count'], 2)

    def test_financial_report_invalid_date_format(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:reports-financial')
        response = self.client.get(url, {'start_date': 'invalid-date'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_financial_report_start_after_end_date(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:reports-financial')
        response = self.client.get(url, {'start_date': '2026-02-01', 'end_date': '2026-01-01'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # 4. TRANSACTION CSV IMPORT TESTS
    # -------------------------------------------------------------------------

    def test_import_transactions_valid_csv(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:import-transactions')

        csv_content = (
            "date,description,amount,transaction_type,category\n"
            "2026-02-01,Freelance Project,1200.00,INCOME,Salary\n"
            "2026-02-02,Weekly Groceries,85.20,EXPENSE,Groceries\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        file_obj.name = 'valid_import.csv'

        response = self.client.post(url, {'file': file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['imported'], 2)
        self.assertEqual(data['failed'], 0)
        self.assertEqual(len(data['errors']), 0)

        # Verify transactions were persisted in database
        self.assertTrue(Transaction.objects.filter(user=self.user1, description='Freelance Project').exists())
        self.assertTrue(Transaction.objects.filter(user=self.user1, description='Weekly Groceries').exists())

    def test_import_transactions_invalid_date_format(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:import-transactions')

        csv_content = (
            "date,description,amount,transaction_type,category\n"
            "02/01/2026,Freelance Project,1200.00,INCOME,Salary\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        file_obj.name = 'invalid_date.csv'

        response = self.client.post(url, {'file': file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()

        self.assertFalse(data['success'])
        self.assertEqual(data['imported'], 0)
        self.assertEqual(data['failed'], 1)
        self.assertIn('field', data['errors'][0])
        self.assertEqual(data['errors'][0]['field'], 'date')

    def test_import_transactions_invalid_amount(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:import-transactions')

        csv_content = (
            "date,description,amount,transaction_type,category\n"
            "2026-02-01,Freelance Project,-100.00,INCOME,Salary\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        file_obj.name = 'invalid_amount.csv'

        response = self.client.post(url, {'file': file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()

        self.assertFalse(data['success'])
        self.assertEqual(data['failed'], 1)
        self.assertEqual(data['errors'][0]['field'], 'amount')

    def test_import_transactions_invalid_type(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:import-transactions')

        csv_content = (
            "date,description,amount,transaction_type,category\n"
            "2026-02-01,Freelance Project,100.00,INVALID_TYPE,Salary\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        file_obj.name = 'invalid_type.csv'

        response = self.client.post(url, {'file': file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors'][0]['field'], 'transaction_type')

    def test_import_transactions_invalid_category(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:import-transactions')

        csv_content = (
            "date,description,amount,transaction_type,category\n"
            "2026-02-01,Unknown Cat Txn,100.00,EXPENSE,NonExistentCategory\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        file_obj.name = 'invalid_category.csv'

        response = self.client.post(url, {'file': file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors'][0]['field'], 'category')

    def test_import_transactions_cross_user_category_rejected(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:import-transactions')

        # Try to use User2's category name or ID
        csv_content = (
            f"date,description,amount,transaction_type,category\n"
            f"2026-02-01,Hacking Attempt,500.00,EXPENSE,{self.cat_user2.name}\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        file_obj.name = 'cross_user_cat.csv'

        response = self.client.post(url, {'file': file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors'][0]['field'], 'category')

    def test_import_transactions_duplicate_in_file(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:import-transactions')

        csv_content = (
            "date,description,amount,transaction_type,category\n"
            "2026-02-10,Coffee Shop,5.50,EXPENSE,Groceries\n"
            "2026-02-10,Coffee Shop,5.50,EXPENSE,Groceries\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        file_obj.name = 'file_duplicates.csv'

        response = self.client.post(url, {'file': file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['imported'], 1)
        self.assertEqual(data['failed'], 1)
        self.assertEqual(data['errors'][0]['field'], 'duplicate')

    def test_import_transactions_duplicate_in_database(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:import-transactions')

        # Try importing txn1 which already exists in database
        csv_content = (
            "date,description,amount,transaction_type,category\n"
            "2026-01-15,Monthly Salary,5000.00,INCOME,Salary\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        file_obj.name = 'db_duplicates.csv'

        response = self.client.post(url, {'file': file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['imported'], 0)
        self.assertEqual(data['failed'], 1)
        self.assertEqual(data['errors'][0]['field'], 'duplicate')

    def test_import_transactions_missing_required_headers(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:import-transactions')

        csv_content = (
            "date,amount\n"
            "2026-02-01,100.00\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        file_obj.name = 'missing_headers.csv'

        response = self.client.post(url, {'file': file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors'][0]['field'], 'header')

    def test_import_transactions_non_csv_file(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('transactions:import-transactions')

        file_obj = io.BytesIO(b"some raw data")
        file_obj.name = 'test_image.png'

        response = self.client.post(url, {'file': file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # 5. SECURITY AND USER ISOLATION TESTS
    # -------------------------------------------------------------------------

    def test_unauthenticated_export_denied(self):
        url = reverse('transactions:export-transactions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_report_denied(self):
        url = reverse('transactions:reports-financial')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_import_denied(self):
        url = reverse('transactions:import-transactions')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
