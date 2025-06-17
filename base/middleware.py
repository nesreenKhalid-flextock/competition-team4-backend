import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse, JsonResponse

# Create a logger for this middleware
logger = logging.getLogger("error_response_logger")


class ErrorResponseLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log response bodies when HTTP status code is >= 400
    """

    def process_response(self, request, response):
        """
        Process the response and log error responses
        """

        # Only log if status code is 400 or higher (client/server errors)
        if response.status_code >= 400:
            print(request.data)
            try:
                # Get request information
                request_method = request.method
                request_path = request.get_full_path()
                status_code = response.status_code

                # Get response content
                response_content = None
                content_type = response.get("Content-Type", "")

                if hasattr(response, "content"):
                    try:
                        # Try to decode as UTF-8
                        response_body = response.content.decode("utf-8")

                        # If it's JSON, try to parse it for better formatting
                        if "application/json" in content_type:
                            try:
                                response_content = json.loads(response_body)
                            except json.JSONDecodeError:
                                response_content = response_body
                        else:
                            response_content = response_body

                    except UnicodeDecodeError:
                        response_content = (
                            f"<Binary content, length: {len(response.content)} bytes>"
                        )

                # Get user information if available
                user_info = "Anonymous"
                if hasattr(request, "user") and request.user.is_authenticated:
                    user_info = (
                        f"User ID: {request.user.id}, Username: {request.user.username}"
                    )

                # Create log entry
                log_data = {
                    "timestamp": None,  # Will be added by logging formatter
                    "request_method": request_method,
                    "request_path": request_path,
                    "status_code": status_code,
                    "user": user_info,
                    "response_content": response_content,
                }

                # Log the error response
                if status_code >= 500:
                    logger.error(
                        f"Server Error Response - {request_method} {request_path} - "
                        f"Status: {status_code} - User: {user_info} - "
                        f"Response: {json.dumps(response_content, indent=2) if isinstance(response_content, (dict, list)) else response_content}"
                    )
                else:
                    logger.warning(
                        f"Client Error Response - {request_method} {request_path} - "
                        f"Status: {status_code} - User: {user_info} - "
                        f"Response: {json.dumps(response_content, indent=2) if isinstance(response_content, (dict, list)) else response_content}"
                    )

            except Exception as e:
                # Don't let middleware errors break the response
                logger.error(f"Error in ErrorResponseLoggingMiddleware: {str(e)}")

        return response
