import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_default_currency():
    """Verify that custom User model defaults currency to LKR."""
    user = User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="SecurePassword123!"
    )
    assert user.currency == "LKR"
    assert user.username == "testuser"
    assert user.email == "testuser@example.com"
    assert user.created_at is not None
    assert str(user) == "testuser@example.com"


@pytest.mark.django_db
def test_custom_user_str_representation():
    """Test user string representation uses email when present, falls back to username."""
    user_with_email = User(username="user1", email="user1@example.com")
    user_without_email = User(username="user2", email="")

    assert str(user_with_email) == "user1@example.com"
    assert str(user_without_email) == "user2"
