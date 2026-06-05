from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.services.auth_utils import role_required, get_current_user
from app.services.payroll import (
    calculate_net_from_gross,
    calculate_gross_from_net,
    compare_contract_types,
    annual_forecast,
)
from app.services.variants import save_variant, get_user_variants, get_variant_for_user

calculator_bp = Blueprint("calculator", __name__)


@calculator_bp.route("/net-from-gross", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def net_from_gross():
    data = request.get_json() or {}
    gross = data.get("gross")
    if gross is None or gross <= 0:
        return jsonify({"error": "Podaj poprawną kwotę brutto (> 0)"}), 400

    result = calculate_net_from_gross(
        gross=float(gross),
        contract_type=data.get("contract_type", "uop"),
        ppk_enabled=data.get("ppk_enabled", True),
        include_sickness=data.get("include_sickness", True),
        custom_deductions=float(data.get("custom_deductions", 0)),
        custom_additions=float(data.get("custom_additions", 0)),
    )
    return jsonify(asdict(result))


@calculator_bp.route("/gross-from-net", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def gross_from_net():
    data = request.get_json() or {}
    net = data.get("net")
    if net is None or net <= 0:
        return jsonify({"error": "Podaj poprawną kwotę netto (> 0)"}), 400

    result = calculate_gross_from_net(
        target_net=float(net),
        contract_type=data.get("contract_type", "uop"),
        ppk_enabled=data.get("ppk_enabled", True),
        include_sickness=data.get("include_sickness", True),
        custom_deductions=float(data.get("custom_deductions", 0)),
        custom_additions=float(data.get("custom_additions", 0)),
    )
    return jsonify(asdict(result))


@calculator_bp.route("/employer-cost", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def employer_cost():
    data = request.get_json() or {}
    gross = data.get("gross")
    if gross is None or gross <= 0:
        return jsonify({"error": "Podaj poprawną kwotę brutto (> 0)"}), 400

    result = calculate_net_from_gross(
        gross=float(gross),
        contract_type=data.get("contract_type", "uop"),
        ppk_enabled=data.get("ppk_enabled", True),
    )
    return jsonify({
        "gross": result.gross,
        "employer_zus": result.employer_zus,
        "fp": result.fp,
        "fgszp": result.fgszp,
        "ppk_employer": result.ppk_employer,
        "total_employer_cost": result.total_employer_cost,
    })


@calculator_bp.route("/compare-contracts", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def compare_contracts():
    data = request.get_json() or {}
    gross = data.get("gross")
    if gross is None or gross <= 0:
        return jsonify({"error": "Podaj poprawną kwotę brutto (> 0)"}), 400
    results = compare_contract_types(float(gross), data.get("ppk_enabled", True))
    return jsonify({"comparisons": results})


@calculator_bp.route("/annual-forecast", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def forecast():
    data = request.get_json() or {}
    gross = data.get("gross")
    if gross is None or gross <= 0:
        return jsonify({"error": "Podaj poprawną kwotę brutto (> 0)"}), 400
    forecast_data = annual_forecast(
        gross=float(gross),
        months=int(data.get("months", 12)),
        salary_growth=float(data.get("salary_growth", 0.05)),
        contract_type=data.get("contract_type", "uop"),
    )
    return jsonify({"forecast": forecast_data})


@calculator_bp.route("/save", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def save_calculation():
    user = get_current_user()
    data = request.get_json() or {}
    name = data.get("name", "Kalkulacja").strip()
    if not data.get("input") or not data.get("result"):
        return jsonify({"error": "Wymagane pola: input, result"}), 400
    variant = save_variant(user.id, name, data.get("type", "payroll"), data["input"], data["result"])
    return jsonify({"id": variant.id, "name": variant.name, "message": "Zapisano"}), 201


@calculator_bp.route("/history", methods=["GET"])
@role_required("user", "admin", "hr_admin")
def history():
    user = get_current_user()
    variant_type = request.args.get("type")
    variants = get_user_variants(user.id, variant_type)
    return jsonify([{
        "id": v.id,
        "name": v.name,
        "type": v.variant_type,
        "created_at": v.created_at.isoformat(),
        "input": v.input_data.data_json if v.input_data else None,
        "result": v.result_data.data_json if v.result_data else None,
    } for v in variants])


@calculator_bp.route("/history/<int:variant_id>", methods=["GET"])
@role_required("user", "admin", "hr_admin")
def get_history_item(variant_id):
    user = get_current_user()
    variant = get_variant_for_user(variant_id, user.id)
    if not variant:
        return jsonify({"error": "Brak dostępu do tego rekordu"}), 403
    return jsonify({
        "id": variant.id,
        "name": variant.name,
        "type": variant.variant_type,
        "created_at": variant.created_at.isoformat(),
        "input": variant.input_data.data_json if variant.input_data else None,
        "result": variant.result_data.data_json if variant.result_data else None,
    })
