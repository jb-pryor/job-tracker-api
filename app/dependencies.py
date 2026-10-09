from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

# Extract the bearer token from the Authorization header.
# tokenUrl tells the API docs where users can obtain a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    # Use the same 401 response for invalid tokens and missing users.
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify the token through our security helper and read its user ID.
        payload = decode_access_token(token)

        user_id = int(payload["sub"])

        if user_id <= 0:
            raise ValueError("Invalid user ID")

    except (InvalidTokenError, ValueError, TypeError, KeyError):
        raise credentials_error from None

    # Look up the user by primary key to confirm the account still exists.
    user = db.get(User, user_id)

    if user is None:
        raise credentials_error

    # Protected endpoints receive this authenticated User through Depends.
    return user