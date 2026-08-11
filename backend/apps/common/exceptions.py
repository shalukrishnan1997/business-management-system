"""
Consistent API error responses.

Shape:
{
  "success": false,
  "message": "Human-readable summary",
  "errors": { ... } | null
}
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {
                "success": False,
                "message": "An unexpected server error occurred.",
                "errors": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    message = "Request failed."
    errors = response.data

    if isinstance(response.data, dict):
        if "detail" in response.data:
            detail = response.data["detail"]
            message = str(detail)
            errors = {"detail": detail}
        else:
            # Field errors — use first message as summary when possible
            first_key = next(iter(response.data), None)
            if first_key is not None:
                first_val = response.data[first_key]
                if isinstance(first_val, (list, tuple)) and first_val:
                    message = str(first_val[0])
                else:
                    message = str(first_val)
    elif isinstance(response.data, list) and response.data:
        message = str(response.data[0])
        errors = {"non_field_errors": response.data}

    response.data = {
        "success": False,
        "message": message,
        "errors": errors,
    }
    return response
