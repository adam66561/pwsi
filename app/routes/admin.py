from datetime import datetime

from flask import Blueprint, jsonify, request

from app import db
from app.models.user import User, UserProfile
from app.models.system import SystemParameter, AuditLog
from app.services.auth_utils import hash_password, role_required, get_current_user
from app.services.audit import log_action
from app.services.parameters import DEFAULT_PARAMETERS, get_parameters
from app.services.variants import cleanup_expired_variants

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@role_required("admin")
def list_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    } for u in users])


@admin_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@role_required("admin")
def change_role(user_id):
    admin = get_current_user()
    data = request.get_json() or {}
    new_role = data.get("role")
    if new_role not in User.ROLES:
        return jsonify({"error": f"Rola musi być jedną z: {User.ROLES}"}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Użytkownik nie istnieje"}), 404
    old_role = user.role
    user.role = new_role
    db.session.commit()
    log_action(admin.id, "CHANGE_ROLE", f"User {user.username}: {old_role} -> {new_role}")
    return jsonify({"message": "Rola zmieniona"})


@admin_bp.route("/users/<int:user_id>/reset", methods=["POST"])
@role_required("admin")
def reset_password(user_id):
    admin = get_current_user()
    data = request.get_json() or {}
    new_password = data.get("password", "reset123")
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Użytkownik nie istnieje"}), 404
    user.password_hash = hash_password(new_password)
    db.session.commit()
    log_action(admin.id, "RESET_PASSWORD", f"Reset hasła dla {user.username}")
    return jsonify({"message": "Hasło zresetowane"})


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_user(user_id):
    admin = get_current_user()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Użytkownik nie istnieje"}), 404
    user.is_active = not user.is_active
    db.session.commit()
    log_action(admin.id, "TOGGLE_USER", f"{user.username} active={user.is_active}")
    return jsonify({"is_active": user.is_active})


@admin_bp.route("/parameters", methods=["GET"])
@role_required("hr_admin", "admin")
def list_parameters():
    params = SystemParameter.query.order_by(SystemParameter.key).all()
    if not params:
        return jsonify(get_parameters())
    return jsonify([{
        "id": p.id,
        "key": p.key,
        "value": p.value,
        "description": p.description,
        "valid_from": p.valid_from.isoformat(),
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    } for p in params])


@admin_bp.route("/parameters/<int:param_id>", methods=["PUT"])
@role_required("hr_admin")
def update_parameter(param_id):
    hr_admin = get_current_user()
    data = request.get_json() or {}
    param = SystemParameter.query.get(param_id)
    if not param:
        return jsonify({"error": "Parametr nie istnieje"}), 404
    new_value = data.get("value")
    valid_from = data.get("valid_from")
    if new_value is None:
        return jsonify({"error": "Podaj nową wartość (value)"}), 400

    old_value = param.value
    param.value = float(new_value)
    if valid_from:
        param.valid_from = datetime.strptime(valid_from, "%Y-%m-%d").date()
    param.updated_by = hr_admin.id
    db.session.commit()
    log_action(
        hr_admin.id,
        "UPDATE_PARAMETER",
        f"{param.key}: {old_value} -> {param.value} (od {param.valid_from})",
    )
    return jsonify({"message": "Parametr zaktualizowany", "key": param.key, "value": param.value})


@admin_bp.route("/parameters/defaults", methods=["GET"])
@role_required("hr_admin", "admin")
def parameter_defaults():
    return jsonify({k: {"value": v[0], "description": v[1]} for k, v in DEFAULT_PARAMETERS.items()})


@admin_bp.route("/audit-log", methods=["GET"])
@role_required("admin", "hr_admin")
def audit_log():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return jsonify([{
        "id": l.id,
        "user_id": l.user_id,
        "action": l.action,
        "details": l.details,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    } for l in logs])


@admin_bp.route("/cleanup", methods=["POST"])
@role_required("admin")
def cleanup():
    count = cleanup_expired_variants()
    log_action(get_current_user().id, "CLEANUP_HISTORY", f"Usunięto {count} wygasłych rekordów")
    return jsonify({"removed": count})
