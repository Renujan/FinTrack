import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from transactions.choices import TransactionType, GoalStatus
from transactions.models import Category, Transaction, FinancialGoal
from transactions.services import GoalCalculationService

User = get_user_model()


class FinancialGoalModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='goaluser',
            email='goaluser@example.com',
            password='password123'
        )
        self.category = Category.objects.create(user=self.user, name='Emergency Savings')

    def test_goal_creation_success(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='Emergency Fund',
            description='Save 6 months of expenses',
            target_amount=Decimal('5000.00'),
            target_date=datetime.date(2026, 12, 31),
            category=self.category,
            is_active=True
        )
        self.assertEqual(goal.name, 'Emergency Fund')
        self.assertEqual(goal.target_amount, Decimal('5000.00'))
        self.assertEqual(goal.category, self.category)
        self.assertTrue(goal.is_active)
        self.assertIn('Emergency Fund', str(goal))

    def test_positive_target_amount(self):
        goal = FinancialGoal(
            user=self.user,
            name='Valid Goal',
            target_amount=Decimal('100.00'),
            target_date=datetime.date(2026, 12, 31)
        )
        goal.full_clean()
        goal.save()
        self.assertEqual(goal.target_amount, Decimal('100.00'))


class GoalCalculationServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='serviceuser',
            email='serviceuser@example.com',
            password='password123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='password123'
        )
        self.cat_savings = Category.objects.create(user=self.user, name='Savings')
        self.cat_investment = Category.objects.create(user=self.user, name='Investments')
        self.other_cat = Category.objects.create(user=self.other_user, name='Savings')

        self.today = datetime.date.today()
        self.future_date = self.today + datetime.timedelta(days=30)
        self.past_date = self.today - datetime.timedelta(days=10)

    def test_zero_progress(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='New Car',
            target_amount=Decimal('1000.00'),
            target_date=self.future_date
        )
        metrics = GoalCalculationService.calculate_goal_metrics(goal)
        self.assertEqual(metrics['current_amount'], Decimal('0.00'))
        self.assertEqual(metrics['remaining_amount'], Decimal('1000.00'))
        self.assertEqual(metrics['percentage_complete'], 0.0)
        self.assertFalse(metrics['is_completed'])
        self.assertEqual(metrics['status'], GoalStatus.ACTIVE)

    def test_partial_progress(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='Vacation',
            target_amount=Decimal('1000.00'),
            target_date=self.future_date
        )
        Transaction.objects.create(
            user=self.user,
            category=self.cat_savings,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('650.00'),
            date=self.today
        )
        metrics = GoalCalculationService.calculate_goal_metrics(goal)
        self.assertEqual(metrics['current_amount'], Decimal('650.00'))
        self.assertEqual(metrics['remaining_amount'], Decimal('350.00'))
        self.assertEqual(metrics['percentage_complete'], 65.0)
        self.assertFalse(metrics['is_completed'])
        self.assertEqual(metrics['status'], GoalStatus.ACTIVE)

    def test_full_and_over_target_progress(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='Laptop',
            target_amount=Decimal('1000.00'),
            target_date=self.future_date
        )
        Transaction.objects.create(
            user=self.user,
            category=self.cat_savings,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('1200.00'),
            date=self.today
        )
        metrics = GoalCalculationService.calculate_goal_metrics(goal)
        self.assertEqual(metrics['current_amount'], Decimal('1200.00'))
        self.assertEqual(metrics['remaining_amount'], Decimal('0.00'))
        self.assertEqual(metrics['percentage_complete'], 120.0)
        self.assertTrue(metrics['is_completed'])
        self.assertEqual(metrics['status'], GoalStatus.COMPLETED)

    def test_expense_exclusion(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='House Deposit',
            target_amount=Decimal('2000.00'),
            target_date=self.future_date
        )
        Transaction.objects.create(
            user=self.user,
            category=self.cat_savings,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('500.00'),
            date=self.today
        )
        metrics = GoalCalculationService.calculate_goal_metrics(goal)
        self.assertEqual(metrics['current_amount'], Decimal('0.00'))

    def test_category_based_contribution(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='Invest',
            category=self.cat_investment,
            target_amount=Decimal('1000.00'),
            target_date=self.future_date
        )
        # Income in different category
        Transaction.objects.create(
            user=self.user,
            category=self.cat_savings,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('500.00'),
            date=self.today
        )
        # Income in matching category
        Transaction.objects.create(
            user=self.user,
            category=self.cat_investment,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('300.00'),
            date=self.today
        )
        metrics = GoalCalculationService.calculate_goal_metrics(goal)
        self.assertEqual(metrics['current_amount'], Decimal('300.00'))

    def test_date_behavior_after_target_date(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='Expired Target',
            target_amount=Decimal('1000.00'),
            target_date=self.past_date
        )
        # Income dated before target date counts
        Transaction.objects.create(
            user=self.user,
            category=self.cat_savings,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('400.00'),
            date=self.past_date
        )
        # Income dated after target date is excluded
        Transaction.objects.create(
            user=self.user,
            category=self.cat_savings,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('500.00'),
            date=self.today
        )
        metrics = GoalCalculationService.calculate_goal_metrics(goal)
        self.assertEqual(metrics['current_amount'], Decimal('400.00'))
        self.assertEqual(metrics['status'], GoalStatus.OVERDUE)

    def test_user_isolation_for_contributions(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='User A Goal',
            target_amount=Decimal('1000.00'),
            target_date=self.future_date
        )
        Transaction.objects.create(
            user=self.other_user,
            category=self.other_cat,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('1000.00'),
            date=self.today
        )
        metrics = GoalCalculationService.calculate_goal_metrics(goal)
        self.assertEqual(metrics['current_amount'], Decimal('0.00'))

    def test_status_paused(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='Paused Goal',
            target_amount=Decimal('1000.00'),
            target_date=self.future_date,
            is_active=False
        )
        metrics = GoalCalculationService.calculate_goal_metrics(goal)
        self.assertEqual(metrics['status'], GoalStatus.PAUSED)


class FinancialGoalAPITests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            username='usera',
            email='usera@example.com',
            password='password123'
        )
        self.user_b = User.objects.create_user(
            username='userb',
            email='userb@example.com',
            password='password123'
        )
        self.cat_a = Category.objects.create(user=self.user_a, name='Category A')
        self.cat_b = Category.objects.create(user=self.user_b, name='Category B')

        self.list_create_url = reverse('transactions:financial-goal-list-create')
        self.today = datetime.date.today()
        self.future_date = self.today + datetime.timedelta(days=30)

        self.client.force_authenticate(user=self.user_a)

    def test_unauthenticated_request_denied(self):
        self.client.logout()
        res = self.client.get(self.list_create_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_goal_success(self):
        data = {
            'name': 'Save for TV',
            'description': '4K OLED TV',
            'target_amount': '1500.00',
            'target_date': str(self.future_date),
            'category': self.cat_a.id,
            'is_active': True
        }
        res = self.client.post(self.list_create_url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Save for TV')
        self.assertEqual(res.data['target_amount'], '1500.00')
        self.assertEqual(res.data['category'], self.cat_a.id)
        self.assertEqual(res.data['status'], GoalStatus.ACTIVE)

    def test_create_goal_using_other_user_category_fails(self):
        data = {
            'name': 'Invalid Goal',
            'target_amount': '500.00',
            'target_date': str(self.future_date),
            'category': self.cat_b.id
        }
        res = self.client.post(self.list_create_url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_goal_invalid_amount_fails(self):
        data = {
            'name': 'Negative Target',
            'target_amount': '-500.00',
            'target_date': str(self.future_date)
        }
        res = self.client.post(self.list_create_url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        data['target_amount'] = '0.00'
        res = self.client.post(self.list_create_url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_goals_user_isolation(self):
        goal_a = FinancialGoal.objects.create(
            user=self.user_a,
            name='Goal A',
            target_amount=Decimal('100.00'),
            target_date=self.future_date
        )
        goal_b = FinancialGoal.objects.create(
            user=self.user_b,
            name='Goal B',
            target_amount=Decimal('200.00'),
            target_date=self.future_date
        )
        res = self.client.get(self.list_create_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], goal_a.id)

    def test_retrieve_goal_detail(self):
        goal = FinancialGoal.objects.create(
            user=self.user_a,
            name='Detail Goal',
            target_amount=Decimal('500.00'),
            target_date=self.future_date
        )
        url = reverse('transactions:financial-goal-detail', kwargs={'pk': goal.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], goal.id)

    def test_update_goal_put_and_patch(self):
        goal = FinancialGoal.objects.create(
            user=self.user_a,
            name='Update Goal',
            target_amount=Decimal('500.00'),
            target_date=self.future_date
        )
        url = reverse('transactions:financial-goal-detail', kwargs={'pk': goal.id})

        patch_res = self.client.patch(url, {'name': 'Updated Name'})
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['name'], 'Updated Name')

        put_res = self.client.put(url, {
            'name': 'Full Update Name',
            'description': 'Updated desc',
            'target_amount': '800.00',
            'target_date': str(self.future_date),
            'is_active': True
        })
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)
        self.assertEqual(put_res.data['name'], 'Full Update Name')

    def test_delete_goal(self):
        goal = FinancialGoal.objects.create(
            user=self.user_a,
            name='Delete Goal',
            target_amount=Decimal('500.00'),
            target_date=self.future_date
        )
        url = reverse('transactions:financial-goal-detail', kwargs={'pk': goal.id})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FinancialGoal.objects.filter(id=goal.id).exists())

    def test_cross_user_access_prevented(self):
        goal_b = FinancialGoal.objects.create(
            user=self.user_b,
            name='Goal B',
            target_amount=Decimal('500.00'),
            target_date=self.future_date
        )
        url = reverse('transactions:financial-goal-detail', kwargs={'pk': goal_b.id})

        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(url, {'name': 'Hacked'}).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_pause_and_resume_actions(self):
        goal = FinancialGoal.objects.create(
            user=self.user_a,
            name='Lifecycle Goal',
            target_amount=Decimal('500.00'),
            target_date=self.future_date,
            is_active=True
        )
        pause_url = reverse('transactions:financial-goal-pause', kwargs={'pk': goal.id})
        resume_url = reverse('transactions:financial-goal-resume', kwargs={'pk': goal.id})

        res_pause = self.client.post(pause_url)
        self.assertEqual(res_pause.status_code, status.HTTP_200_OK)
        self.assertFalse(res_pause.data['is_active'])
        self.assertEqual(res_pause.data['status'], GoalStatus.PAUSED)

        res_resume = self.client.post(resume_url)
        self.assertEqual(res_resume.status_code, status.HTTP_200_OK)
        self.assertTrue(res_resume.data['is_active'])
        self.assertEqual(res_resume.data['status'], GoalStatus.ACTIVE)

    def test_cross_user_pause_resume_prevented(self):
        goal_b = FinancialGoal.objects.create(
            user=self.user_b,
            name='User B Goal',
            target_amount=Decimal('500.00'),
            target_date=self.future_date
        )
        pause_url = reverse('transactions:financial-goal-pause', kwargs={'pk': goal_b.id})
        self.assertEqual(self.client.post(pause_url).status_code, status.HTTP_404_NOT_FOUND)


class GoalFilteringSearchingOrderingPaginationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='filteruser',
            email='filteruser@example.com',
            password='password123'
        )
        self.cat_1 = Category.objects.create(user=self.user, name='House')
        self.cat_2 = Category.objects.create(user=self.user, name='Car')

        self.client.force_authenticate(user=self.user)
        self.today = datetime.date.today()

        self.g1 = FinancialGoal.objects.create(
            user=self.user,
            name='Alpha Goal',
            description='Save for house',
            target_amount=Decimal('10000.00'),
            target_date=self.today + datetime.timedelta(days=100),
            category=self.cat_1,
            is_active=True
        )
        self.g2 = FinancialGoal.objects.create(
            user=self.user,
            name='Beta Goal',
            description='Buy sports car',
            target_amount=Decimal('5000.00'),
            target_date=self.today + datetime.timedelta(days=50),
            category=self.cat_2,
            is_active=False
        )

        self.list_url = reverse('transactions:financial-goal-list-create')

    def test_filter_by_is_active(self):
        res = self.client.get(self.list_url, {'is_active': 'true'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['id'], self.g1.id)

    def test_filter_by_category(self):
        res = self.client.get(self.list_url, {'category': 'House'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['id'], self.g1.id)

    def test_search_by_goal_name_or_description(self):
        res = self.client.get(self.list_url, {'search': 'sports car'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['id'], self.g2.id)

    def test_ordering_by_target_amount(self):
        res = self.client.get(self.list_url, {'ordering': 'target_amount'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data['results']
        self.assertEqual(results[0]['id'], self.g2.id)
        self.assertEqual(results[1]['id'], self.g1.id)

    def test_ordering_by_percentage_complete(self):
        Transaction.objects.create(
            user=self.user,
            category=self.cat_2,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('4000.00'),
            date=self.today
        )
        res = self.client.get(self.list_url, {'ordering': '-percentage_complete'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data['results']
        self.assertEqual(results[0]['id'], self.g2.id)

    def test_pagination_response_structure(self):
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('count', res.data)
        self.assertIn('next', res.data)
        self.assertIn('previous', res.data)
        self.assertIn('results', res.data)
