from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import jwt

from crypto.key import get_pem

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

type JSON = dict[str, JSON | list[JSON] | str | float | int | bool | None]


class JWTGenerator:
    """Generates JSON Web Tokens (JWTs) signed with an Ed25519 private key."""

    def __init__(self, issuer: str, private_key: Ed25519PrivateKey) -> None:
        self._issuer: str = issuer
        self._priv: bytes = get_pem(private_key)

    def generate(
        self,
        *,
        website: str,
        challenge_id: str,
        valid_duration: float = 600,
        **kwargs: JSON,
    ) -> str:
        """Generate JWT token based on website and challenge_id and any addition attributes.

        Returns:
            str: The generated JWT token as a string.

        """
        data = {
            **kwargs,
            "challenge_id": challenge_id,
        }
        current = datetime.now(UTC)
        data["nbf"] = current.timestamp()  # Not before timestamp
        data["exp"] = (current + timedelta(seconds=valid_duration)).timestamp()  # Expiration timestamp
        data["aud"] = website  # Audience (the website domain)
        data["iss"] = self._issuer  # The issue (the CAPTCHA server domain)
        data["iat"] = current.timestamp()  # Issue timestamp

        return jwt.encode(data, self._priv, algorithm="EdDSA")


class JWTValidator:
    """Validates JSON Web Tokens (JWTs) using an Ed25519 public key."""

    def __init__(self, public_key: Ed25519PublicKey) -> None:
        self._pub: bytes = get_pem(public_key)

    def validate(self, token: str, audience: str | None = None) -> dict[str, JSON]:
        """Validate JWT token and return the payload.

        Args:
            token: The JWT token to validate
            audience: Expected audience (optional)

        Returns:
            dict: The validated JWT payload

        Raises:
            jwt.InvalidTokenError: If the token is invalid
            jwt.ExpiredSignatureError: If the token has expired
            jwt.InvalidAudienceError: If the audience doesn't match

        """
        options = {"verify_signature": True, "verify_exp": True, "verify_nbf": True}

        if audience:
            return jwt.decode(
                token,
                self._pub,
                algorithms=["EdDSA"],
                audience=audience,
                options=options,
            )
        return jwt.decode(
            token,
            self._pub,
            algorithms=["EdDSA"],
            options=options,
        )
