import bcrypt
from flask_jwt_extended import get_jwt_identity

from app.models.user import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_current_user() -> User | None:
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    return User.query.get(int(user_id))


def role_required(*roles):
    from functools import wraps
    from flask import jsonify
    from flask_jwt_extended import verify_jwt_in_request

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if not user or not user.is_active:
                return jsonify({"error": "Brak autoryzacji"}), 401
            if user.role not in roles:
                return jsonify({"error": "Brak uprawnień"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
