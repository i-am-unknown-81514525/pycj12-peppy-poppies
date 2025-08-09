from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import jwt

from .key import get_pem

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

type JSON = dict[str, JSON | list[JSON] | str | float | int | bool | None]

class JWTGenerator:
    """Generates JSON Web Tokens (JWTs) signed with an Ed25519 private key."""
    def __init__(self, issuer: str, private_key: Ed25519PrivateKey) -> None:
        self._issuer: str = issuer
        self._priv: bytes = get_pem(private_key)

    def generate(
        self, *, website: str, session_id: str, challenge_id: str, valid_duration: float = 600, **kwargs : JSON,
    ) -> str:
        """Generate JWT token based on website, session_id and challenge_id and any addition attributes."""

        data = {
            **kwargs,
            "session_id": session_id,
            "challenge_id": challenge_id,
        }
        current = datetime.now(UTC)
        data["nbf"] = current.timestamp()  # Not before timestamp
        data["exp"] = (current + timedelta(seconds=valid_duration)).timestamp()  # Expiration timestamp
        data["aud"] = website  # Audience (the website domain)
        data["iss"] = self._issuer  # The issue (the CAPTCHA server domain)
        data["iat"] = current.timestamp()  # Issue timestamp

        return jwt.encode(data, self._priv, algorithm="EdDSA")
