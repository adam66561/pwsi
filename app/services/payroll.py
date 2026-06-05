"""Logika kalkulacji wynagrodzeń zgodna z polskimi przepisami (UoP, UZ, UoD)."""

from dataclasses import dataclass, asdict

from app.services.parameters import get_parameters


@dataclass
class PayrollBreakdown:
    gross: float
    net: float
    zus_employee: float
    health: float
    pit: float
    ppk_employee: float
    employer_zus: float
    fp: float
    fgszp: float
    ppk_employer: float
    total_employer_cost: float
    contract_type: str
    details: dict


def _get_uop_kup(params: dict, cost_type: str) -> float:
    if cost_type == "raised":
        return params["uop_kup_raised_monthly"]
    if cost_type == "none":
        return 0.0
    return params["uop_kup_standard_monthly"]


def _get_part_tax_reducing_amount(tax_free_mode: str) -> float:
    if tax_free_mode == "none":
        return 0.0
    if tax_free_mode == "one_employer":
        return 12.0
    if tax_free_mode == "two_employers":
        return 24.0
    if tax_free_mode == "three_employers":
        return 36.0

    return 12.0

def _calc_pit(
    tax_basis: float,
    params: dict,
    sum_up_tax_basis: float = 0.0,
    part_tax_reducing_amount: float = 12.0,
) -> float:
    """Oblicza miesięczną zaliczkę PIT według skali.
    tax_basis - podstawa PIT za bieżący miesiąc
    sum_up_tax_basis - podstawa PIT narastająco z poprzednich miesięcy
    part_tax_reducing_amount:
        0  - bez kwoty zmniejszającej
        12 - standardowo 300 zł miesięcznie
        24 - 150 zł miesięcznie
        36 - 100 zł miesięcznie
        1  - cała roczna kwota zmniejszająca
    """

    tax_basis = max(0, tax_basis)
    sum_up_tax_basis = max(0, sum_up_tax_basis)

    first_limit = params["pit_first_limit_annual"]
    first_rate = params["pit_first_rate"]
    second_rate = params["pit_second_rate"]

    if sum_up_tax_basis > first_limit:
        tax_amount = tax_basis * second_rate

    elif sum_up_tax_basis + tax_basis > first_limit:
        first_part = first_limit - sum_up_tax_basis
        second_part = tax_basis + sum_up_tax_basis - first_limit

        tax_amount = first_part * first_rate
        tax_amount += second_part * second_rate

    else:
        tax_amount = tax_basis * first_rate

    if part_tax_reducing_amount:
        tax_amount -= params["tax_reduction_annual"] / part_tax_reducing_amount

    return round(max(0, tax_amount), 0)


def calculate_net_from_gross(
    gross: float,
    contract_type: str = "uop",
    ppk_enabled: bool = True,
    include_sickness: bool = True,
    custom_deductions: float = 0.0,
    custom_additions: float = 0.0,

    tax_free_mode: str = "one_employer",
    cost_type: str = "standard",
    sum_up_tax_basis: float = 0.0,
) -> PayrollBreakdown:
    params = get_parameters()
    gross = round(gross + custom_additions, 2)

    part_tax_reducing_amount = _get_part_tax_reducing_amount(tax_free_mode)

    if contract_type == "uod":
        return _calculate_uod(
            gross,
            params,
            custom_deductions,
            part_tax_reducing_amount,
            sum_up_tax_basis,
        )

    if contract_type == "uz":
        return _calculate_uz(
            gross,
            params,
            custom_deductions,
            include_sickness,
            part_tax_reducing_amount,
            sum_up_tax_basis,
        )

    return _calculate_uop(
        gross,
        params,
        ppk_enabled,
        include_sickness,
        custom_deductions,
        part_tax_reducing_amount,
        cost_type,
        sum_up_tax_basis,
    )


def _calculate_uop(
    gross: float,
    params: dict,
    ppk_enabled: bool,
    include_sickness: bool,
    deductions: float,
    part_tax_reducing_amount: float,
    cost_type: str,
    sum_up_tax_basis: float,
) -> PayrollBreakdown:
    zus_emerytalna = round(gross * params["zus_emerytalna_employee"], 2)
    zus_rentowa = round(gross * params["zus_rentowa_employee"], 2)
    zus_chorobowa = round(gross * params["zus_chorobowa_employee"], 2) if include_sickness else 0.0

    social_contributions = round(zus_emerytalna + zus_rentowa + zus_chorobowa, 2)

    health_base = round(gross - social_contributions, 2)
    health = round(health_base * params["health_rate"], 2)

    ppk_employee = round(gross * params["ppk_employee_rate"], 2) if ppk_enabled else 0.0

    kup = _get_uop_kup(params, cost_type)

    tax_basis = round(gross - social_contributions - kup - deductions, 2)
    tax_basis = max(0, tax_basis)

    pit = _calc_pit(
        tax_basis=tax_basis,
        params=params,
        sum_up_tax_basis=sum_up_tax_basis,
        part_tax_reducing_amount=part_tax_reducing_amount,
    )

    net = round(gross - social_contributions - health - pit - ppk_employee - deductions, 2)

    employer_emerytalna = round(gross * params["zus_emerytalna_employer"], 2)
    employer_rentowa = round(gross * params["zus_rentowa_employer"], 2)
    employer_wypadkowa = round(gross * params["zus_wypadkowa_employer"], 2)

    employer_zus = round(
        employer_emerytalna + employer_rentowa + employer_wypadkowa,
        2,
    )

    fp = round(gross * params["fp_rate"], 2)
    # fs = round(gross * params["fs_rate"], 2)
    fs = 0.0
    fgszp = round(gross * params["fgszp_rate"], 2)

    ppk_employer = round(gross * params["ppk_employer_rate"], 2) if ppk_enabled else 0.0

    total_employer_cost = round(
        gross + employer_zus + fp + fs + fgszp + ppk_employer,
        2,
    )

    return PayrollBreakdown(
        gross=gross,
        net=net,
        zus_employee=social_contributions,
        health=health,
        pit=pit,
        ppk_employee=ppk_employee,
        employer_zus=employer_zus,
        fp=round(fp + fs, 2),
        fgszp=fgszp,
        ppk_employer=ppk_employer,
        total_employer_cost=total_employer_cost,
        contract_type="uop",
        details={
            "zus_emerytalna": zus_emerytalna,
            "zus_rentowa": zus_rentowa,
            "zus_chorobowa": zus_chorobowa,
            "zus_employee_total": social_contributions,

            "gross_minus_zus": round(gross - social_contributions, 2),  

            "health_base": health_base,
            "health": health,
            "health_deductible": 0.0,

            "kup": kup,
            "tax_basis": tax_basis,
            "tax_basis_rounded": round(tax_basis),

            "pit_before_rounding": pit,
            "pit": round(pit),

            "employer_emerytalna": employer_emerytalna,
            "employer_rentowa": employer_rentowa,
            "employer_wypadkowa": employer_wypadkowa,
            "employer_zus_total": employer_zus,

            "fp": fp,
            "fs": fs,
            "fp_fs_total": round(fp + fs, 2),

            "fgszp": fgszp,
            "additional_employer_cost": round(employer_zus + fp + fs + fgszp + ppk_employer, 2),
        },
    )


def _calculate_uz(
    gross: float,
    params: dict,
    deductions: float,
    include_sickness: bool,
    part_tax_reducing_amount: float,
    sum_up_tax_basis: float,
) -> PayrollBreakdown:
    zus_emerytalna = round(gross * params["uz_emerytalna_employee"], 2)
    zus_rentowa = round(gross * params["uz_rentowa_employee"], 2)
    zus_chorobowa = round(gross * params["uz_chorobowa_employee"], 2) if include_sickness else 0.0

    social_contributions = round(zus_emerytalna + zus_rentowa + zus_chorobowa, 2)
    gross_minus_zus = round(gross - social_contributions, 2)
    
    health_base = round(gross - social_contributions, 2)
    health = round(health_base * params["health_rate"], 2)

    kup = round((gross - social_contributions) * params["uz_kup_rate"], 2)

    tax_basis = round(gross - social_contributions - kup - deductions, 2)
    tax_basis = max(0, tax_basis)

    pit = _calc_pit(
        tax_basis=tax_basis,
        params=params,
        sum_up_tax_basis=sum_up_tax_basis,
        part_tax_reducing_amount=part_tax_reducing_amount,
    )

    net = round(gross - social_contributions - health - pit - deductions, 2)

    employer_emerytalna = round(gross * params["uz_emerytalna_employer"], 2)
    employer_rentowa = round(gross * params["uz_rentowa_employer"], 2)
    employer_wypadkowa = round(gross * params["uz_wypadkowa_employer"], 2)

    employer_zus = round(
        employer_emerytalna + employer_rentowa + employer_wypadkowa,
        2,
    )

    total_employer_cost = round(gross + employer_zus, 2)

    return PayrollBreakdown(
        gross=gross,
        net=net,
        zus_employee=social_contributions,
        health=health,
        pit=pit,
        ppk_employee=0.0,
        employer_zus=employer_zus,
        fp=0.0,
        fgszp=0.0,
        ppk_employer=0.0,
        total_employer_cost=total_employer_cost,
        contract_type="uz",
        details={
            "zus_emerytalna": zus_emerytalna,
            "zus_rentowa": zus_rentowa,
            "zus_chorobowa": zus_chorobowa,
            "zus_employee_total": social_contributions,

            "gross_minus_zus": gross_minus_zus,

            "health_base": health_base,
            "health": health,
            "health_deductible": 0.0,

            "kup": kup,
            "tax_basis": tax_basis,
            "tax_basis_rounded": round(tax_basis),

            "employer_emerytalna": employer_emerytalna,
            "employer_rentowa": employer_rentowa,
            "employer_wypadkowa": employer_wypadkowa,
            "employer_zus_total": employer_zus,

            "additional_employer_cost": employer_zus,
        },
    )


def _calculate_uod(
    gross: float,
    params: dict,
    deductions: float,
    part_tax_reducing_amount: float,
    sum_up_tax_basis: float,
) -> PayrollBreakdown:
    costs = round(gross * params["uod_kup_rate"], 2)

    tax_basis = round(gross - costs - deductions, 2)
    tax_basis = max(0, tax_basis)

    pit = _calc_pit(
        tax_basis=tax_basis,
        params=params,
        sum_up_tax_basis=sum_up_tax_basis,
        part_tax_reducing_amount=part_tax_reducing_amount,
    )

    net = round(gross - pit - deductions, 2)

    return PayrollBreakdown(
        gross=gross,
        net=net,
        zus_employee=0.0,
        health=0.0,
        pit=pit,
        ppk_employee=0.0,
        employer_zus=0.0,
        fp=0.0,
        fgszp=0.0,
        ppk_employer=0.0,
        total_employer_cost=gross,
        contract_type="uod",
        details={
            "costs": costs,
            "tax_basis": tax_basis,
            "sum_up_tax_basis": sum_up_tax_basis,
            "part_tax_reducing_amount": part_tax_reducing_amount,
        },
    )


def calculate_gross_from_net(
    target_net: float,
    contract_type: str = "uop",
    ppk_enabled: bool = True,
    include_sickness: bool = True,
    custom_deductions: float = 0.0,
    custom_additions: float = 0.0,
    tolerance: float = 0.01,
    max_iterations: int = 100,
) -> PayrollBreakdown:
    """Oblicza brutto metodą bisekcji na podstawie kwoty netto."""
    low, high = target_net, target_net * 3
    result = None

    for _ in range(max_iterations):
        mid = round((low + high) / 2, 2)
        result = calculate_net_from_gross(
            mid, contract_type, ppk_enabled, include_sickness, custom_deductions, custom_additions
        )
        diff = result.net - target_net
        if abs(diff) <= tolerance:
            return result
        if diff < 0:
            low = mid
        else:
            high = mid

    return result


def compare_contract_types(gross: float, ppk_enabled: bool = True) -> list[dict]:
    results = []
    for ct in ("uop", "uz", "uod"):
        breakdown = calculate_net_from_gross(gross, contract_type=ct, ppk_enabled=ppk_enabled)
        results.append(asdict(breakdown))
    return results


def annual_forecast(
    gross: float,
    months: int = 12,
    salary_growth: float = 0.05,
    contract_type: str = "uop",
) -> list[dict]:
    forecast = []
    current_gross = gross
    for month in range(1, months + 1):
        breakdown = calculate_net_from_gross(current_gross, contract_type=contract_type)
        forecast.append({
            "month": month,
            "gross": breakdown.gross,
            "net": breakdown.net,
            "pit": breakdown.pit,
            "zus": breakdown.zus_employee,
            "health": breakdown.health,
        })
        if month % 12 == 0:
            current_gross = round(current_gross * (1 + salary_growth), 2)
    return forecast
