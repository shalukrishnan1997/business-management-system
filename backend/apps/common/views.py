from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Unauthenticated smoke endpoint for Phase 2 verification.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "Business Management System API is running.",
                "data": {
                    "service": "bms-api",
                    "version": "1.0.0",
                    "phase": 2,
                },
            }
        )
