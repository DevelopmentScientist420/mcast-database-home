from collections import OrderedDict
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

"""
Dictionary which allows Swagger UI in the CSP
"""
CSP: dict[str, str | list[str]] = {
    "default-src": "'self'",
    "img-src": [
        "*",
        # For SWAGGER UI
        "data:",
    ],
    "connect-src": "'self'",
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "script-src-elem": [
        "'self'",
        "'unsafe-inline'",
        # For SWAGGER UI
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"
    ],
    "style-src-elem": [
        # For SWAGGER UI
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    ],
}


def parse_policy(policy: dict[str, str | list[str]] | str) -> str:
    """
    Parse the CSP policy into a string.
    :param policy: CSP policy as a dict or string
    :return: CSP policy as a string
    """
    if isinstance(policy, str):
        # parse the string into a policy dict
        policy_string = policy
        policy = OrderedDict()

        for policy_part in policy_string.split(";"):
            policy_parts = policy_part.strip().split(" ")
            policy[policy_parts[0]] = " ".join(policy_parts[1:])

    policies = []
    for section, content in policy.items():
        if not isinstance(content, str):
            content = " ".join(content)
        policy_part = f"{section} {content}"

        policies.append(policy_part)

    parsed_policy = "; ".join(policies)

    return parsed_policy


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    def __init__(self, app: FastAPI, csp: bool = True) -> None:
        """Init SecurityHeadersMiddleware.

        :param app: FastAPI instance
        :param no_csp: If no CSP should be used;
            defaults to :py:obj:`False`
        """
        super().__init__(app)
        self.csp = csp

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Dispatch of the middleware.

        :param request: Incoming request
        :param call_next: Function to process the request
        :return: Return response coming from processed request
        """
        headers = {
            "Content-Security-Policy": "" if not self.csp else parse_policy(CSP),
            "Cross-Origin-Opener-Policy": "same-origin",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Strict-Transport-Security": "max-age=31556926; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
        }
        response = await call_next(request)
        response.headers.update(headers)

        return response
