from litestar import Request, get
from litestar.controller import Controller


class ProtectedController(Controller):
    """Controller for protected routes that require JWT authentication."""
    
    path = "/api/protected"
    tags = ["Protected"]

    @get("/profile")
    async def get_profile(self, request: Request) -> dict:
        """Get user profile information from JWT token.
        
        This endpoint requires a valid JWT token in the Authorization header.
        
        Returns:
            dict: User profile information from JWT payload
        """
        # The JWT payload is added to the request scope by the middleware
        jwt_payload = request.scope.get("jwt_payload", {})
        
        return {
            "message": "Access granted to protected resource",
            "jwt_payload": jwt_payload,
            "user_info": {
                "challenge_id": jwt_payload.get("challenge_id"),
                "audience": jwt_payload.get("aud"),
                "issuer": jwt_payload.get("iss"),
                "issued_at": jwt_payload.get("iat"),
                "expires_at": jwt_payload.get("exp")
            }
        }

    @get("/data")
    async def get_protected_data(self, request: Request) -> dict:
        """Get some protected data.
        
        This endpoint requires a valid JWT token in the Authorization header.
        
        Returns:
            dict: Protected data
        """
        jwt_payload = request.scope.get("jwt_payload", {})
        
        return {
            "message": "This is protected data",
            "data": {
                "secret_value": "42",
                "protected_info": "Only authenticated users can see this",
                "challenge_verified": True
            },
            "authenticated_user": {
                "challenge_id": jwt_payload.get("challenge_id"),
                "verified_at": jwt_payload.get("iat")
            }
        }
