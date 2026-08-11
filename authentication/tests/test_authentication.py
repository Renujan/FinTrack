import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
        "password_confirm": "SecurePassword123!",
        "currency": "USD",
    }


@pytest.fixture
def create_user(user_data):
    user = User.objects.create_user(
        username=user_data["username"],
        email=user_data["email"],
        password=user_data["password"],
        currency=user_data["currency"],
    )
    return user


@pytest.mark.django_db
class TestAuthenticationAPI:

    def test_registration_success(self, api_client, user_data):
        url = reverse("auth:register")
        response = api_client.post(url, user_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["message"] == "User registered successfully"
        assert response.data["user"]["username"] == user_data["username"]
        assert response.data["user"]["email"] == user_data["email"]
        assert response.data["user"]["currency"] == "USD"
        assert User.objects.filter(email=user_data["email"]).exists()

    def test_registration_duplicate_email(self, api_client, create_user, user_data):
        url = reverse("auth:register")
        response = api_client.post(url, user_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data or "non_field_errors" in response.data

    def test_registration_password_mismatch(self, api_client, user_data):
        url = reverse("auth:register")
        user_data["password_confirm"] = "DifferentPassword123!"
        response = api_client.post(url, user_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data

    def test_login_success(self, api_client, create_user, user_data):
        url = reverse("auth:login")
        login_payload = {
            "username": user_data["username"],
            "password": user_data["password"],
        }
        response = api_client.post(url, login_payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_password(self, api_client, create_user, user_data):
        url = reverse("auth:login")
        login_payload = {
            "username": user_data["username"],
            "password": "WrongPassword123!",
        }
        response = api_client.post(url, login_payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh(self, api_client, create_user, user_data):
        login_url = reverse("auth:login")
        login_res = api_client.post(
            login_url,
            {"username": user_data["username"], "password": user_data["password"]},
            format="json",
        )
        refresh_token = login_res.data["refresh"]

        refresh_url = reverse("auth:token_refresh")
        response = api_client.post(refresh_url, {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_profile_access_unauthenticated(self, api_client):
        url = reverse("auth:profile")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_access_authenticated(self, api_client, create_user):
        api_client.force_authenticate(user=create_user)
        url = reverse("auth:profile")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == create_user.username
        assert response.data["email"] == create_user.email
        assert response.data["currency"] == create_user.currency

    def test_profile_update(self, api_client, create_user):
        api_client.force_authenticate(user=create_user)
        url = reverse("auth:profile")
        update_data = {"currency": "EUR"}
        response = api_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["currency"] == "EUR"

        create_user.refresh_from_db()
        assert create_user.currency == "EUR"

    def test_logout_blacklists_token(self, api_client, create_user, user_data):
        login_url = reverse("auth:login")
        login_res = api_client.post(
            login_url,
            {"username": user_data["username"], "password": user_data["password"]},
            format="json",
        )
        refresh_token = login_res.data["refresh"]
        access_token = login_res.data["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_url = reverse("auth:logout")
        response = api_client.post(logout_url, {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Successfully logged out"

        # Attempting to refresh using blacklisted refresh token should fail
        refresh_url = reverse("auth:token_refresh")
        api_client.credentials()  # Clear credentials
        refresh_res = api_client.post(refresh_url, {"refresh": refresh_token}, format="json")
        assert refresh_res.status_code == status.HTTP_401_UNAUTHORIZED
