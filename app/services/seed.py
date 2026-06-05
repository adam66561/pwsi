from datetime import date

from app import db
from app.models.user import User, UserProfile
from app.models.system import SystemParameter
from app.services.auth_utils import hash_password
from app.services.parameters import DEFAULT_PARAMETERS


def seed_database():
    if not SystemParameter.query.first():
        for key, (value, description) in DEFAULT_PARAMETERS.items():
            db.session.add(SystemParameter(
                key=key,
                value=value,
                description=description,
                valid_from=date(2025, 1, 1),
            ))
        db.session.commit()

    demo_users = [
        ("user", "user@pwsi.pl", "user123", "Jan", "Kowalski", "user"),
        ("admin", "admin@pwsi.pl", "admin123", "Admin", "Techniczny", "admin"),
        ("hr_admin", "hr@pwsi.pl", "hr12345", "Anna", "Nowak", "hr_admin"),
    ]
    for username, email, password, first, last, role in demo_users:
        if not User.query.filter_by(username=username).first():
            user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                role=role,
            )
            db.session.add(user)
            db.session.flush()
            db.session.add(UserProfile(
                user_id=user.id,
                first_name=first,
                last_name=last,
            ))
    db.session.commit()
