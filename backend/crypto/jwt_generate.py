from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import jwt

from .key import get_pem

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

class JWTGenerator:
    def __init__(self, issuer: str, private_key: Ed25519PrivateKey) -> None:
        self._issuer: str = issuer
        self._priv: bytes = get_pem(private_key)


    def generate(self, *, website: str, session_id: str, challenge_id: str, valid_duration: int = 600, **kwargs) -> str:
        data = {
            **kwargs,
            "session_id": session_id,
            "challenge_id": challenge_id,
        }
        current = datetime.now(timezone.utc)
        data["nbf"] = current.timestamp() # Not before timestamp
        data["exp"] = (current + timedelta(seconds=valid_duration)).timestamp() # Expiration timestamp
        data["aud"] = website # Audience (the website domain)
        data["iss"] = self._issuer # The issue (the CAPTCHA server domain)
        data["iat"] = current.timestamp() # Issue timestamp

        jwt_token = jwt.encode(
            data,
            self._priv,
            algorithm="EdDSA"
        )
        return jwt_token
