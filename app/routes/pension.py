from flask import Blueprint, jsonify, request

from app.services.auth_utils import role_required, get_current_user
from app.services.pension import simulate_pension, pension_to_dict
from app.services.variants import save_variant

pension_bp = Blueprint("pension", __name__)


@pension_bp.route("/simulate", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def simulate():
    data = request.get_json() or {}
    try:
        result = simulate_pension(
            current_age=int(data.get("current_age", 30)),
            gender=data.get("gender", "M"),
            retirement_age=int(data.get("retirement_age", 67)),
            gross_salary=float(data.get("gross_salary", 8000)),
            work_years=int(data.get("work_years", 5)),
            zus_capital=float(data.get("zus_capital", 0)),
            ofe_member=bool(data.get("ofe_member", False)),
            ofe_capital=float(data.get("ofe_capital", 0)),
            ofe_option=data.get("ofe_option", "stay"),
            ppk_enabled=bool(data.get("ppk_enabled", True)),
            ppk_capital=float(data.get("ppk_capital", 0)),
            salary_growth=data.get("salary_growth"),
            inflation=data.get("inflation"),
            ofe_return=data.get("ofe_return"),
            ppk_return=data.get("ppk_return"),
            planned_expenses=float(data.get("planned_expenses", 5000)),
        )
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(pension_to_dict(result))


@pension_bp.route("/save", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def save_simulation():
    user = get_current_user()
    data = request.get_json() or {}
    name = data.get("name", "Symulacja emerytury").strip()
    if not data.get("input") or not data.get("result"):
        return jsonify({"error": "Wymagane pola: input, result"}), 400
    variant = save_variant(user.id, name, "pension", data["input"], data["result"])
    return jsonify({"id": variant.id, "name": variant.name, "message": "Zapisano"}), 201
