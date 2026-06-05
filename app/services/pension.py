"""Symulacja emerytury ZUS, OFE i PPK."""

from dataclasses import dataclass, asdict

from app.services.parameters import get_parameters
from app.services.payroll import calculate_net_from_gross


@dataclass
class PensionResult:
    zus_monthly_pension: float
    ofe_monthly_pension: float
    ppk_monthly_payout: float
    total_monthly_pension: float
    retirement_age: int
    years_to_retirement: int
    final_zus_capital: float
    final_ofe_capital: float
    final_ppk_capital: float
    capital_growth: list[dict]
    scenarios: dict
    expense_coverage: float = 0.0
    planned_expenses: float = 0.0
    inflation_adjusted_pension: float = 0.0

def _get_life_expectancy_months(gender: str, params: dict) -> float:
    """Zwraca uproszczone dalsze trwanie życia w miesiącach."""
    if gender.upper() == "F":
        return params.get("life_expectancy_months_female", params["life_expectancy_female"] * 12)

    return params.get("life_expectancy_months_male", params["life_expectancy_male"] * 12)

def _get_contribution_rates(ofe_member: bool, ofe_option: str, params: dict) -> tuple[float, float]:
    """Zwraca stawkę składki do ZUS i OFE.

    Nie wolno dodawać pełnych 19,52% do ZUS i jeszcze osobno OFE,
    bo wtedy składka emerytalna jest liczona podwójnie.
    """

    pension_rate = params.get("pension_contribution_rate", 0.1952)
    ofe_rate = params.get("ofe_contribution_rate", 0.0292)

    if ofe_member and ofe_option == "stay":
        zus_rate = pension_rate - ofe_rate
        return zus_rate, ofe_rate

    return pension_rate, 0.0

def simulate_pension(
    current_age: int,
    gender: str,
    retirement_age: int,
    gross_salary: float,
    work_years: int,
    zus_capital: float,
    ofe_member: bool = False,
    ofe_capital: float = 0.0,
    ofe_option: str = "stay",
    ppk_enabled: bool = True,
    ppk_capital: float = 0.0,
    salary_growth: float | None = None,
    inflation: float | None = None,
    ofe_return: float | None = None,
    ppk_return: float | None = None,
    planned_expenses: float = 5000.0,
) -> PensionResult:
    params = get_parameters()

    salary_growth = salary_growth if salary_growth is not None else params["default_salary_growth"]
    inflation = inflation if inflation is not None else params["default_inflation"]
    ofe_return = ofe_return if ofe_return is not None else params["ofe_return_rate"]
    ppk_return = ppk_return if ppk_return is not None else params["ppk_return_rate"]

    zus_indexation = params.get("zus_indexation_rate", 0.03)

    if current_age < 18 or current_age > 80:
        raise ValueError("Wiek musi być w zakresie 18–80 lat")

    if retirement_age <= current_age or retirement_age > 80:
        raise ValueError("Planowany wiek emerytalny musi być większy od aktualnego wieku i ≤ 80")

    if gross_salary <= 0:
        raise ValueError("Wynagrodzenie brutto musi być większe od 0")

    if work_years < 0:
        raise ValueError("Staż pracy nie może być ujemny")

    if zus_capital < 0 or ofe_capital < 0 or ppk_capital < 0:
        raise ValueError("Kapitał nie może być ujemny")

    years_to_retirement = retirement_age - current_age
    life_months = _get_life_expectancy_months(gender, params)

    capital_growth = []

    current_gross = gross_salary
    current_zus = zus_capital
    current_ofe = ofe_capital if ofe_member else 0.0
    current_ppk = ppk_capital

    active_ofe = ofe_member

    if active_ofe and ofe_option == "transfer":
        current_zus += current_ofe
        current_ofe = 0.0
        active_ofe = False

    for year in range(1, years_to_retirement + 1):
        age = current_age + year - 1
        annual_salary = current_gross * 12

        zus_rate, ofe_rate = _get_contribution_rates(active_ofe, ofe_option, params)

        zus_contribution = annual_salary * zus_rate
        ofe_contribution = annual_salary * ofe_rate

        current_zus = current_zus * (1 + zus_indexation) + zus_contribution

        if active_ofe and ofe_option == "stay":
            current_ofe = current_ofe * (1 + ofe_return) + ofe_contribution

        if ppk_enabled:
            ppk_contribution = annual_salary * (
                params["ppk_employee_rate"] + params["ppk_employer_rate"]
            )
            current_ppk = current_ppk * (1 + ppk_return) + ppk_contribution
        else:
            ppk_contribution = 0.0

        capital_growth.append({
            "year": year,
            "age": age,
            "gross_salary": round(current_gross, 2),
            "annual_salary": round(annual_salary, 2),

            "zus_contribution": round(zus_contribution, 2),
            "ofe_contribution": round(ofe_contribution, 2),
            "ppk_contribution": round(ppk_contribution, 2),

            "zus_capital": round(current_zus, 2),
            "ofe_capital": round(current_ofe, 2),
            "ppk_capital": round(current_ppk, 2),
        })

        current_gross = round(current_gross * (1 + salary_growth), 2)

    zus_monthly = round(current_zus / life_months, 2)
    ofe_monthly = round(current_ofe / life_months, 2) if current_ofe > 0 else 0.0

    # To nie jest emerytura z ZUS, tylko uproszczona miesięczna wypłata z kapitału PPK.
    ppk_monthly = round(current_ppk / life_months, 2) if ppk_enabled else 0.0

    total_monthly = round(zus_monthly + ofe_monthly + ppk_monthly, 2)

    scenarios = _build_scenarios(
        current_age=current_age,
        gender=gender,
        retirement_age=retirement_age,
        gross_salary=gross_salary,
        zus_capital=zus_capital,
        ofe_capital=ofe_capital,
        ppk_capital=ppk_capital,
        ppk_enabled=ppk_enabled,
        params=params,
        ofe_member=ofe_member,
        ofe_option=ofe_option,
        salary_growth=salary_growth,
        ofe_return=ofe_return,
        ppk_return=ppk_return,
    )

    inflation_adjusted_pension = round(
        total_monthly / ((1 + inflation) ** years_to_retirement),
        2,
    )

    expense_coverage = (
        round(inflation_adjusted_pension / planned_expenses * 100, 1)
        if planned_expenses > 0
        else 0.0
    )

    return PensionResult(
        zus_monthly_pension=zus_monthly,
        ofe_monthly_pension=ofe_monthly,
        ppk_monthly_payout=ppk_monthly,
        total_monthly_pension=total_monthly,
        retirement_age=retirement_age,
        years_to_retirement=years_to_retirement,
        final_zus_capital=round(current_zus, 2),
        final_ofe_capital=round(current_ofe, 2),
        final_ppk_capital=round(current_ppk, 2),
        capital_growth=capital_growth,
        scenarios=scenarios,
        expense_coverage=expense_coverage,
        planned_expenses=planned_expenses,
        inflation_adjusted_pension=inflation_adjusted_pension,
    )


def _compute_pension_core(
    current_age: int,
    gender: str,
    retirement_age: int,
    gross_salary: float,
    zus_capital: float,
    ofe_capital: float,
    ppk_capital: float,
    ppk_enabled: bool,
    params: dict,
    ofe_member: bool,
    ofe_option: str,
    salary_growth: float,
    ofe_return: float,
    ppk_return: float,
) -> tuple[float, float, float]:
    years_to_retirement = retirement_age - current_age
    life_months = _get_life_expectancy_months(gender, params)

    zus_indexation = params.get("zus_indexation_rate", 0.03)

    current_gross = gross_salary
    current_zus = zus_capital
    current_ofe = ofe_capital if ofe_member else 0.0
    current_ppk = ppk_capital

    active_ofe = ofe_member

    if active_ofe and ofe_option == "transfer":
        current_zus += current_ofe
        current_ofe = 0.0
        active_ofe = False

    for _ in range(years_to_retirement):
        annual_salary = current_gross * 12

        zus_rate, ofe_rate = _get_contribution_rates(active_ofe, ofe_option, params)

        zus_contribution = annual_salary * zus_rate
        ofe_contribution = annual_salary * ofe_rate

        current_zus = current_zus * (1 + zus_indexation) + zus_contribution

        if active_ofe and ofe_option == "stay":
            current_ofe = current_ofe * (1 + ofe_return) + ofe_contribution

        if ppk_enabled:
            ppk_contribution = annual_salary * (
                params["ppk_employee_rate"] + params["ppk_employer_rate"]
            )
            current_ppk = current_ppk * (1 + ppk_return) + ppk_contribution

        current_gross = round(current_gross * (1 + salary_growth), 2)

    zus_monthly = round(current_zus / life_months, 2)
    ofe_monthly = round(current_ofe / life_months, 2) if current_ofe > 0 else 0.0
    ppk_monthly = round(current_ppk / life_months, 2) if ppk_enabled else 0.0

    return zus_monthly, ofe_monthly, ppk_monthly


def _build_scenarios(
    current_age: int,
    gender: str,
    retirement_age: int,
    gross_salary: float,
    zus_capital: float,
    ofe_capital: float,
    ppk_capital: float,
    ppk_enabled: bool,
    params: dict,
    ofe_member: bool,
    ofe_option: str,
    salary_growth: float,
    ofe_return: float,
    ppk_return: float,
) -> dict:
    scenarios = {}

    scenario_defs = [
        ("pesymistyczny", -2, -0.02),
        ("bazowy", 0, 0.0),
        ("optymistyczny", 3, 0.02),
    ]

    for name, ret_age_delta, growth_delta in scenario_defs:
        adj_ret_age = retirement_age + ret_age_delta

        if adj_ret_age <= current_age:
            continue

        adj_growth = max(0.0, salary_growth + growth_delta)

        try:
            zus_m, ofe_m, ppk_m = _compute_pension_core(
                current_age=current_age,
                gender=gender,
                retirement_age=adj_ret_age,
                gross_salary=gross_salary,
                zus_capital=zus_capital,
                ofe_capital=ofe_capital,
                ppk_capital=ppk_capital,
                ppk_enabled=ppk_enabled,
                params=params,
                ofe_member=ofe_member,
                ofe_option=ofe_option,
                salary_growth=adj_growth,
                ofe_return=ofe_return,
                ppk_return=ppk_return,
            )

            total = round(zus_m + ofe_m + ppk_m, 2)

            scenarios[name] = {
                "retirement_age": adj_ret_age,
                "salary_growth": round(adj_growth, 4),
                "total_monthly_pension": total,
                "zus_monthly": zus_m,
                "ofe_monthly": ofe_m,
                "ppk_monthly": ppk_m,
            }

        except (ValueError, ZeroDivisionError):
            continue

    return scenarios


def pension_to_dict(result: PensionResult) -> dict:
    return asdict(result)