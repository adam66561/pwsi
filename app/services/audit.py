from app import db
from app.models.system import AuditLog


def log_action(user_id: int | None, action: str, details: str = ""):
    entry = AuditLog(user_id=user_id, action=action, details=details)
    db.session.add(entry)
    db.session.commit()
