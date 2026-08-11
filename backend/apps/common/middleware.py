"""
Authenticate JWT on the Django request so middleware (e.g. audit) sees request.user.
"""


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if header.startswith("Bearer "):
            try:
                from rest_framework_simplejwt.authentication import JWTAuthentication

                result = JWTAuthentication().authenticate(request)
                if result is not None:
                    request.user, request.auth = result
            except Exception:
                pass
        return self.get_response(request)
