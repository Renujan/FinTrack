from django.test import TestCase
from transactions.choices import TransactionType


class TransactionTypeChoicesTest(TestCase):
    def test_transaction_type_choices(self):
        self.assertEqual(TransactionType.INCOME, 'INCOME')
        self.assertEqual(TransactionType.EXPENSE, 'EXPENSE')
        self.assertEqual(TransactionType.INCOME.label, 'Income')
        self.assertEqual(TransactionType.EXPENSE.label, 'Expense')
        self.assertIn(('INCOME', 'Income'), TransactionType.choices)
        self.assertIn(('EXPENSE', 'Expense'), TransactionType.choices)
