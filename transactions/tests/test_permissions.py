from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from transactions.permissions import IsOwner

User = get_user_model()


class PermissionsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsOwner()
        self.user1 = User.objects.create_user(email='perm1@example.com', password='Password123!', username='perm1')
        self.user2 = User.objects.create_user(email='perm2@example.com', password='Password123!', username='perm2')
        self.obj_user1 = SimpleNamespace(user=self.user1)

    def test_owner_has_permission(self):
        request = self.factory.get('/')
        request.user = self.user1
        self.assertTrue(self.permission.has_object_permission(request, None, self.obj_user1))

    def test_non_owner_denied_permission(self):
        request = self.factory.get('/')
        request.user = self.user2
        self.assertFalse(self.permission.has_object_permission(request, None, self.obj_user1))
