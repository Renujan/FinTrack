import pytest
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User
from transactions.models import Category, Transaction, Budget, FinancialGoal, RecurringTransaction, Notification, AuditLog
from transactions.choices import AuditAction, TransactionType
from transactions.audit_services import AuditLogService, get_client_ip


@pytest.fixture
def user(db):
    return User.objects.create_user(username='audit_user', email='audit@test.com', password='password123')


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username='other_audit_user', email='other_audit@test.com', password='password123')


@pytest.mark.django_db
class TestAuditLogModelAndService:
    def test_audit_log_model_creation(self, user):
        log = AuditLog.objects.create(
            user=user,
            action=AuditAction.CREATE,
            resource_type='Transaction',
            resource_id='101',
            ip_address='127.0.0.1',
            metadata={'amount': '150.00'}
        )
        assert log.id is not None
        assert log.user == user
        assert log.action == AuditAction.CREATE
        assert log.resource_type == 'Transaction'
        assert log.resource_id == '101'
        assert log.ip_address == '127.0.0.1'
        assert str(log).startswith("CREATE - Transaction")

    def test_audit_service_log_action_safely(self, user):
        log = AuditLogService.log_action(
            user=user,
            action=AuditAction.UPDATE,
            resource_type='Budget',
            resource_id='50',
            ip_address='192.168.1.1',
            metadata={'name': 'Groceries', 'password': 'secret_password', 'token': 'jwt_token'}
        )
        assert log is not None
        assert log.action == AuditAction.UPDATE
        assert 'password' not in log.metadata
        assert 'token' not in log.metadata
        assert log.metadata['name'] == 'Groceries'

    def test_audit_service_helper_methods(self, user):
        c_log = AuditLogService.log_create(user, 'Category', '1', metadata={'name': 'Food'})
        u_log = AuditLogService.log_update(user, 'Category', '1', metadata={'name': 'Dining'})
        d_log = AuditLogService.log_delete(user, 'Category', '1', metadata={'name': 'Dining'})
        imp_log = AuditLogService.log_import(user, 'Transaction', metadata={'count': 5})
        exp_log = AuditLogService.log_export(user, 'Transaction', metadata={'format': 'csv'})
        login_log = AuditLogService.log_login(user)
        logout_log = AuditLogService.log_logout(user)
        pwd_log = AuditLogService.log_password_change(user)

        assert c_log.action == AuditAction.CREATE
        assert u_log.action == AuditAction.UPDATE
        assert d_log.action == AuditAction.DELETE
        assert imp_log.action == AuditAction.IMPORT
        assert exp_log.action == AuditAction.EXPORT
        assert login_log.action == AuditAction.LOGIN
        assert logout_log.action == AuditAction.LOGOUT
        assert pwd_log.action == AuditAction.PASSWORD_CHANGE

    def test_client_ip_extraction(self, rf):
        request = rf.get('/api/test/', HTTP_X_FORWARDED_FOR='203.0.113.195, 70.41.3.18')
        ip = get_client_ip(request)
        assert ip == '203.0.113.195'

        request_direct = rf.get('/api/test/', REMOTE_ADDR='198.51.100.1')
        assert get_client_ip(request_direct) == '198.51.100.1'


@pytest.mark.django_db
class TestAuditLogAPI:
    def test_audit_log_list_and_user_isolation(self, user, other_user):
        client = APIClient()
        client.force_authenticate(user=user)

        AuditLogService.log_create(user, 'Transaction', '1')
        AuditLogService.log_update(user, 'Transaction', '1')
        AuditLogService.log_create(other_user, 'Transaction', '2')

        url = reverse('transactions:audit-log-list')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data['results'] if 'results' in response.data else response.data
        assert len(data) == 2
        for log in data:
            assert log['user'] == user.id

    def test_audit_log_filtering_and_ordering(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        AuditLogService.log_create(user, 'Transaction', '1')
        AuditLogService.log_export(user, 'Transaction', metadata={'export_type': 'csv'})

        url = reverse('transactions:audit-log-list')
        response = client.get(url, {'action': 'EXPORT'})

        assert response.status_code == status.HTTP_200_OK
        data = response.data['results'] if 'results' in response.data else response.data
        assert len(data) == 1
        assert data[0]['action'] == 'EXPORT'

    def test_audit_log_detail_view_and_owner_permission(self, user, other_user):
        client = APIClient()
        client.force_authenticate(user=user)

        user_log = AuditLogService.log_create(user, 'Category', '10')
        other_log = AuditLogService.log_create(other_user, 'Category', '20')

        detail_url = reverse('transactions:audit-log-detail', kwargs={'pk': user_log.pk})
        res = client.get(detail_url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data['id'] == user_log.pk

        other_detail_url = reverse('transactions:audit-log-detail', kwargs={'pk': other_log.pk})
        res_other = client.get(other_detail_url)
        assert res_other.status_code == status.HTTP_404_NOT_FOUND
