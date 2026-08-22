from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

from finance_tracker.throttling import AuthRateThrottle, UserAuthRateThrottle
from transactions.audit_services import AuditLogService
from authentication.serializers import RegisterSerializer, UserProfileSerializer


class AuditLogTokenObtainPairView(TokenObtainPairView):
    """
    Subclass of SimpleJWT TokenObtainPairView to apply rate limiting and audit logging on login.
    """
    throttle_classes = [AuthRateThrottle]

    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            username = request.data.get('username')
            from users.models import User
            try:
                user = User.objects.get(username=username)
                AuditLogService.log_login(user, request=request)
            except User.DoesNotExist:
                pass
        return res


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        AuditLogService.log_create(user, 'User', user.id, metadata={'username': user.username}, request=request)
        return Response(
            {
                "message": "User registered successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "currency": user.currency
                }
            },
            status=status.HTTP_201_CREATED
        )


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserAuthRateThrottle]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            AuditLogService.log_logout(request.user, request=request)
            return Response(
                {"message": "Successfully logged out"},
                status=status.HTTP_200_OK
            )
        except TokenError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
