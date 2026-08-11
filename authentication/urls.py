from django.urls import path
from authentication.views import RegisterView

app_name = 'authentication'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
]
