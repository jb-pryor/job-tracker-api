import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

# Load local environment settings; deployed settings can come from the host.
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is not set.")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Use pwdlib's recommended password hashing configuration.
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    # Generate a salted hash to store instead of the original password.
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    # Check a submitted password against its stored hash.
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # "sub" identifies the user; "exp" sets the token's expiration.
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    # Sign the payload with our secret key. JWT contents are not encrypted.
    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    # Verify the signature and expiration, requiring both user ID and expiration.
    # Invalid or expired tokens raise an exception handled by get_current_user.
    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["sub", "exp"]},
    )