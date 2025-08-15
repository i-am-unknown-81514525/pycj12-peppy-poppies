import tempfile
from os import getenv
from pathlib import Path

import httpx
from crypto.jwt_generate import JWTValidator
from crypto.key import import_public_key
from litestar import Request
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.base import AbstractMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send

CAPTCHA_SERVER = getenv("CODECAPTCHA_DOMAIN_INTERNAL", getenv("CODECAPTCHA_DOMAIN", "localhost:8001"))


class JWTValidationError(Exception):
    """Custom exception for JWT validation errors."""


def _raise_public_key_error() -> None:
    """Raise an error for public key retrieval failure."""
    raise JWTValidationError("Failed to retrieve public key from captcha server")


class JWTAuthMiddleware(AbstractMiddleware):
    """JWT Authentication middleware for protected routes."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._jwt_validator = None
        self.protected_paths = ["/api/protected"]  # Add paths that require authentication

    def _is_protected_path(self, path: str) -> bool:
        """Check if the path requires authentication."""
        return any(path.startswith(protected) for protected in self.protected_paths)

    async def _get_jwt_validator(self) -> JWTValidator:
        """Get or create JWT validator with public key from captcha server."""
        if self._jwt_validator is None:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"http://{CAPTCHA_SERVER}/api/challenge/get-public-key")
                    if not resp.is_success:
                        _raise_public_key_error()

                    public_key_data = resp.json()
                    public_key_pem = public_key_data["public_key"]

                    # Save public key temporarily using secure temp file
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as temp_file:
                        temp_file.write(public_key_pem)
                        temp_key_path = Path(temp_file.name)

                    try:
                        # Import and create validator
                        public_key = import_public_key(temp_key_path)
                        self._jwt_validator = JWTValidator(public_key)
                    finally:
                        # Clean up temp file
                        temp_key_path.unlink(missing_ok=True)

            except JWTValidationError:
                raise
            except Exception as e:
                raise JWTValidationError(f"Failed to initialize JWT validator: {e!s}") from e

        return self._jwt_validator

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the request through JWT authentication if needed."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        # Check if this path requires authentication
        if not self._is_protected_path(request.url.path):
            await self.app(scope, receive, send)
            return

        # Extract JWT token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise NotAuthorizedException("Missing or invalid authorization header")

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            # Validate the JWT token
            jwt_validator = await self._get_jwt_validator()
            host = request.headers.get("Host", "localhost")
            payload = jwt_validator.validate(token, audience=host)

            # Add the validated payload to the request scope for use in handlers
            scope["jwt_payload"] = payload

        except JWTValidationError as e:
            raise NotAuthorizedException(f"JWT validation failed: {e!s}") from e
        except Exception as e:
            raise NotAuthorizedException(f"Invalid token: {e!s}") from e

        # Continue to the next middleware/handler
        await self.app(scope, receive, send)
