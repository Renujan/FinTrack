from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers

from finance_tracker.throttling import AuthRateThrottle, UserAuthRateThrottle
from transactions.audit_services import AuditLogService
from authentication.serializers import RegisterSerializer, UserProfileSerializer


@extend_schema(
    tags=['Authentication'],
    summary='Obtain JWT Access & Refresh Tokens (Login)',
    description='Authenticates user credentials and returns JWT access and refresh tokens. Logs login audit events upon success.',
    responses={
        200: inline_serializer(
            name='TokenObtainResponse',
            fields={
                'access': serializers.CharField(),
                'refresh': serializers.CharField(),
            }
        ),
        401: OpenApiResponse(description='Invalid credentials'),
        429: OpenApiResponse(description='Rate limit exceeded'),
    }
)
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


@extend_schema(
    tags=['Authentication'],
    summary='Register a New User',
    description='Registers a new user account with default subscription tier, email, password, and currency preference.',
    request=RegisterSerializer,
    responses={
        201: inline_serializer(
            name='RegisterSuccessResponse',
            fields={
                'message': serializers.CharField(default='User registered successfully'),
                'user': inline_serializer(
                    name='RegisteredUserDetail',
                    fields={
                        'id': serializers.IntegerField(),
                        'username': serializers.CharField(),
                        'email': serializers.EmailField(),
                        'currency': serializers.CharField(),
                    }
                )
            }
        ),
        400: OpenApiResponse(description='Validation error or existing username/email'),
    }
)
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


@extend_schema(
    tags=['Authentication'],
    summary='Blacklist Refresh Token (Logout)',
    description='Blacklists the provided JWT refresh token to revoke future access.',
    request=inline_serializer(
        name='LogoutRequest',
        fields={'refresh': serializers.CharField(help_text='JWT Refresh Token')}
    ),
    responses={
        200: inline_serializer(
            name='LogoutSuccessResponse',
            fields={'message': serializers.CharField(default='Successfully logged out')}
        ),
        400: OpenApiResponse(description='Missing or invalid refresh token'),
        401: OpenApiResponse(description='Authentication credentials were not provided'),
    }
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


@extend_schema(
    tags=['Authentication'],
    summary='Retrieve or Update Current User Profile',
    description='Retrieves or updates authenticated user details including email, name, and currency configuration.',
    responses={
        200: UserProfileSerializer,
        400: OpenApiResponse(description='Invalid profile update data'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

