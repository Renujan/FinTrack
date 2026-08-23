from django.urls import path
from .views import (
    SubscriptionDetailView,
    SubscriptionUsageView,
    SubscriptionPlanListView,
    SubscriptionUpgradeView,
    SubscriptionCancelView,
)

app_name = 'subscriptions'

urlpatterns = [
    path('', SubscriptionDetailView.as_view(), name='detail'),
    path('usage/', SubscriptionUsageView.as_view(), name='usage'),
    path('plans/', SubscriptionPlanListView.as_view(), name='plans'),
    path('upgrade/', SubscriptionUpgradeView.as_view(), name='upgrade'),
    path('cancel/', SubscriptionCancelView.as_view(), name='cancel'),
]
