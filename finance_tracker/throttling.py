from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """
    Throttle rate for unauthenticated login/register/auth endpoints.
    """
    scope = 'auth'


class UserAuthRateThrottle(UserRateThrottle):
    """
    Throttle rate for authenticated user security endpoints (e.g. logout/password change).
    """
    scope = 'auth'


class AnalyticsRateThrottle(UserRateThrottle):
    """
    Throttle rate for high-computation analytics and report generation endpoints.
    """
    scope = 'analytics'


class ImportExportRateThrottle(UserRateThrottle):
    """
    Throttle rate for bulk financial import and export endpoints.
    """
    scope = 'import_export'
