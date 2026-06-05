from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from app import db
from app.models.user import User, UserProfile
from app.services.auth_utils import hash_password, check_password, get_current_user, role_required
from app.services.audit import log_action

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "Wymagane: username, email, password"}), 400
    if len(password) < 6:
        return jsonify({"error": "Hasło musi mieć co najmniej 6 znaków"}), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Użytkownik o podanej nazwie lub emailu już istnieje"}), 409

    user = User(username=username, email=email, password_hash=hash_password(password), role="user")
    db.session.add(user)
    db.session.flush()
    db.session.add(UserProfile(user_id=user.id))
    db.session.commit()

    return jsonify({"message": "Konto utworzone", "user_id": user.id}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()
    if not user or not check_password(password, user.password_hash):
        return jsonify({"error": "Niepoprawny login lub hasło"}), 401
    if not user.is_active:
        return jsonify({"error": "Konto jest nieaktywne"}), 403

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    profile = user.profile
    return jsonify({
        "access_token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "profile": {
                "first_name": profile.first_name if profile else None,
                "last_name": profile.last_name if profile else None,
                "age": profile.age if profile else 30,
                "gender": profile.gender if profile else "M",
                "planned_retirement_age": profile.planned_retirement_age if profile else 67,
                "default_gross_salary": profile.default_gross_salary if profile else 8000,
            } if profile else {},
        },
    })


@auth_bp.route("/me", methods=["GET"])
@role_required("user", "admin", "hr_admin")
def me():
    user = get_current_user()
    profile = user.profile
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "profile": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "age": profile.age,
            "gender": profile.gender,
            "planned_retirement_age": profile.planned_retirement_age,
            "default_gross_salary": profile.default_gross_salary,
            "work_years": profile.work_years,
            "zus_capital": profile.zus_capital,
            "ofe_member": profile.ofe_member,
            "ofe_capital": profile.ofe_capital,
            "ofe_option": profile.ofe_option,
            "ppk_enabled": profile.ppk_enabled,
        } if profile else {},
    })


@auth_bp.route("/profile", methods=["PUT"])
@role_required("user", "admin", "hr_admin")
def update_profile():
    user = get_current_user()
    data = request.get_json() or {}
    profile = user.profile or UserProfile(user_id=user.id)
    for field in ("first_name", "last_name", "age", "gender", "planned_retirement_age",
                  "default_gross_salary", "work_years", "zus_capital", "ofe_member",
                  "ofe_capital", "ofe_option", "ppk_enabled"):
        if field in data:
            setattr(profile, field, data[field])
    if not user.profile:
        db.session.add(profile)
    db.session.commit()
    return jsonify({"message": "Profil zaktualizowany"})
