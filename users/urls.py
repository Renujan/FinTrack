from django.urls import path
from users.views import (
    UserProfileDetailView,
    UserPreferenceDetailView,
    PasswordChangeView,
    AccountOverviewView,
)

app_name = 'users'

urlpatterns = [
    path('profile/', UserProfileDetailView.as_view(), name='profile'),
    path('preferences/', UserPreferenceDetailView.as_view(), name='preferences'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('overview/', AccountOverviewView.as_view(), name='overview'),
]
