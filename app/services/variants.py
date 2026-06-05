from datetime import datetime, timedelta, timezone

from app import db
from app.config import Config
from app.models.calculation import CalculationVariant, CalculationInput, CalculationResult


def save_variant(user_id: int, name: str, variant_type: str, input_data: dict, result_data: dict) -> CalculationVariant:
    expires_at = datetime.now(timezone.utc) + timedelta(days=Config.HISTORY_RETENTION_DAYS)
    variant = CalculationVariant(
        user_id=user_id,
        name=name,
        variant_type=variant_type,
        expires_at=expires_at,
    )
    db.session.add(variant)
    db.session.flush()
    db.session.add(CalculationInput(variant_id=variant.id, data_json=input_data))
    db.session.add(CalculationResult(variant_id=variant.id, data_json=result_data))
    db.session.commit()
    return variant


def get_user_variants(user_id: int, variant_type: str | None = None) -> list[CalculationVariant]:
    query = CalculationVariant.query.filter_by(user_id=user_id)
    if variant_type:
        query = query.filter_by(variant_type=variant_type)
    return query.order_by(CalculationVariant.created_at.desc()).all()


def get_variant_for_user(variant_id: int, user_id: int) -> CalculationVariant | None:
    return CalculationVariant.query.filter_by(id=variant_id, user_id=user_id).first()


def cleanup_expired_variants():
    now = datetime.now(timezone.utc)
    expired = CalculationVariant.query.filter(CalculationVariant.expires_at < now).all()
    for v in expired:
        db.session.delete(v)
    db.session.commit()
    return len(expired)
