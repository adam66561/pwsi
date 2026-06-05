from datetime import datetime, timezone

from app import db


class CalculationVariant(db.Model):
    __tablename__ = "calculation_variants"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    variant_type = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="variants")
    input_data = db.relationship("CalculationInput", back_populates="variant", uselist=False)
    result_data = db.relationship("CalculationResult", back_populates="variant", uselist=False)


class CalculationInput(db.Model):
    __tablename__ = "calculation_inputs"

    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, db.ForeignKey("calculation_variants.id"), unique=True)
    data_json = db.Column(db.JSON, nullable=False)

    variant = db.relationship("CalculationVariant", back_populates="input_data")


class CalculationResult(db.Model):
    __tablename__ = "calculation_results"

    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, db.ForeignKey("calculation_variants.id"), unique=True)
    data_json = db.Column(db.JSON, nullable=False)

    variant = db.relationship("CalculationVariant", back_populates="result_data")
