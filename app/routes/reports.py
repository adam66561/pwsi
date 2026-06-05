from dataclasses import asdict

from flask import Blueprint, jsonify, request, send_file
import io

from app.services.auth_utils import role_required
from app.services.payroll import calculate_net_from_gross, compare_contract_types, annual_forecast
from app.services.pension import simulate_pension, pension_to_dict
from app.services.pdf_report import generate_payroll_pdf, generate_pension_pdf

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/payslip", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def payslip():
    data = request.get_json() or {}
    gross = data.get("gross")
    if not gross or gross <= 0:
        return jsonify({"error": "Podaj poprawną kwotę brutto"}), 400
    result = calculate_net_from_gross(
        gross=float(gross),
        contract_type=data.get("contract_type", "uop"),
        ppk_enabled=data.get("ppk_enabled", True),
    )
    breakdown = asdict(result)
    return jsonify({
        "title": "Pasek wynagrodzeń",
        "contract_type": result.contract_type,
        "breakdown": breakdown,
        "summary": {
            "gross": result.gross,
            "deductions": round(result.zus_employee + result.health + result.pit + result.ppk_employee, 2),
            "net": result.net,
        },
    })


@reports_bp.route("/payslip/pdf", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def payslip_pdf():
    data = request.get_json() or {}
    gross = data.get("gross")
    if not gross or gross <= 0:
        return jsonify({"error": "Podaj poprawną kwotę brutto"}), 400
    result = calculate_net_from_gross(gross=float(gross), contract_type=data.get("contract_type", "uop"))
    pdf_bytes = generate_payroll_pdf(asdict(result))
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="raport_wynagrodzenia.pdf",
    )


@reports_bp.route("/pension/pdf", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def pension_pdf():
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
            planned_expenses=float(data.get("planned_expenses", 5000)),
        )
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    pdf_bytes = generate_pension_pdf(pension_to_dict(result))
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="prognoza_emerytury.pdf",
    )


@reports_bp.route("/comparison", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def comparison_report():
    data = request.get_json() or {}
    gross = data.get("gross")
    if not gross or gross <= 0:
        return jsonify({"error": "Podaj poprawną kwotę brutto"}), 400
    results = compare_contract_types(float(gross))
    best = max(results, key=lambda x: x["net"])
    return jsonify({
        "gross": gross,
        "comparisons": results,
        "recommendation": f"Najwyższe netto: {best['contract_type'].upper()} ({best['net']:.2f} PLN)",
    })


@reports_bp.route("/annual", methods=["POST"])
@role_required("user", "admin", "hr_admin")
def annual_report():
    data = request.get_json() or {}
    gross = data.get("gross")
    if not gross or gross <= 0:
        return jsonify({"error": "Podaj poprawną kwotę brutto"}), 400
    forecast_data = annual_forecast(
        gross=float(gross),
        months=int(data.get("months", 12)),
        salary_growth=float(data.get("salary_growth", 0.05)),
    )
    total_net = sum(m["net"] for m in forecast_data)
    total_gross = sum(m["gross"] for m in forecast_data)
    return jsonify({
        "forecast": forecast_data,
        "summary": {
            "total_gross": round(total_gross, 2),
            "total_net": round(total_net, 2),
            "avg_net": round(total_net / len(forecast_data), 2),
        },
    })
