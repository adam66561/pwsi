from datetime import datetime, timezone

from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="user")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    profile = db.relationship("UserProfile", back_populates="user", uselist=False)
    variants = db.relationship("CalculationVariant", back_populates="user")

    ROLES = ("user", "admin", "hr_admin")


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    age = db.Column(db.Integer, default=30)
    gender = db.Column(db.String(10), default="M")
    planned_retirement_age = db.Column(db.Integer, default=67)
    default_gross_salary = db.Column(db.Float, default=8000.0)
    work_years = db.Column(db.Integer, default=5)
    zus_capital = db.Column(db.Float, default=50000.0)
    ofe_member = db.Column(db.Boolean, default=False)
    ofe_capital = db.Column(db.Float, default=0.0)
    ofe_option = db.Column(db.String(20), default="stay")
    ppk_enabled = db.Column(db.Boolean, default=True)

    user = db.relationship("User", back_populates="profile")
