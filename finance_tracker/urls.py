"""
URL configuration for finance_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from finance_tracker.views import health_check

from users.views import UserProfileDetailView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),

    # OpenAPI Schema & Documentation Endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Core API Routes
    path('api/profile/', UserProfileDetailView.as_view(), name='api-profile'),
    path('api/account/', include('users.urls', namespace='account')),
    path('api/auth/', include('authentication.urls', namespace='auth')),
    path('api/users/', include('users.urls', namespace='users')),
    path('api/subscription/', include('subscriptions.urls', namespace='subscriptions')),
    path('api/', include('transactions.urls', namespace='transactions')),

    # API v1 Route Aliases for Versioning Readiness
    path('api/v1/health/', health_check, name='v1-health-check'),
    path('api/v1/profile/', UserProfileDetailView.as_view(), name='v1-api-profile'),
    path('api/v1/account/', include('users.urls', namespace='v1-account')),
    path('api/v1/auth/', include('authentication.urls', namespace='v1-auth')),
    path('api/v1/users/', include('users.urls', namespace='v1-users')),
    path('api/v1/subscription/', include('subscriptions.urls', namespace='v1-subscriptions')),
    path('api/v1/', include('transactions.urls', namespace='v1-transactions')),
]


