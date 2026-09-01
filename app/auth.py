import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import database, schemas

SECRET_KEY = "your-secret-key-change-in-production"  # In production, use environment variable
TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days

security = HTTPBearer(auto_error=False)

# In-memory token store (in production, use Redis or database)
# token -> user_id
token_store = {}


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a salt."""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}:{hash_obj.hexdigest()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, hash_val = password_hash.split(":")
        hash_obj = hashlib.sha256((password + salt).encode())
        return hash_obj.hexdigest() == hash_val
    except ValueError:
        return False


def create_token(user_id: int) -> str:
    """Create a simple token and store it."""
    token = secrets.token_urlsafe(32)
    token_store[token] = user_id
    return token


def validate_token(token: str) -> Optional[int]:
    """Validate token and return user_id if valid."""
    return token_store.get(token)


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    """Get user by username."""
    with database.get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    """Get user by email."""
    with database.get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def create_user(username: str, email: str, password: str) -> int:
    """Create a new user and return user_id."""
    password_hash = hash_password(password)
    with database.get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        return cursor.lastrowid


def authenticate_user(username: str, password: str) -> Optional[sqlite3.Row]:
    """Authenticate user and return user row if valid."""
    user = get_user_by_username(username)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[sqlite3.Row]:
    """Get current user from token if provided, otherwise return None for guest."""
    if not credentials:
        return None

    token = credentials.credentials
    user_id = validate_token(token)
    if not user_id:
        return None

    with database.get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> sqlite3.Row:
    """Get current user from token, raise 401 if invalid."""
    token = credentials.credentials
    user_id = validate_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    with database.get_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user


def logout_user(token: str) -> bool:
    """Remove token from store."""
    if token in token_store:
        del token_store[token]
        return True
    return False