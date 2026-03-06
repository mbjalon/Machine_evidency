from functools import wraps
from typing import Optional
from flask import session, flash, redirect, url_for


# --- Role permissions ---

ROLE_PERMISSIONS = {
    'admin':     {'view', 'add', 'edit', 'remove'},
    'superuser': {'view', 'add', 'edit'},
    'user':      {'view'},
}

# --- Hardcoded users (replace with DB-backed auth in production) ---

class User:
    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role


USERS = [
    User('user',  '1234',   'user'),
    User('admin', 'Incap1', 'admin'),
    User('peter', 'peter1', 'superuser'),
]


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Return the matching User or None if credentials are invalid."""
    return next(
        (u for u in USERS if u.username == username and u.password == password),
        None,
    )


def check_permission(permission: str, user_role: str) -> bool:
    """Return True if the given role has the requested permission."""
    return permission in ROLE_PERMISSIONS.get(user_role, set())


# --- Decorators ---

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            flash('You need to log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated