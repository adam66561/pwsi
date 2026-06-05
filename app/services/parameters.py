from datetime import date

from app.models.system import SystemParameter

DEFAULT_PARAMETERS = {
    "zus_emerytalna_employee": (0.0976, "Składka emerytalna pracownika"),
    "zus_rentowa_employee": (0.015, "Składka rentowa pracownika"),
    "zus_chorobowa_employee": (0.0245, "Składka chorobowa pracownika"),

    "zus_emerytalna_employer": (0.0976, "Składka emerytalna pracodawcy"),
    "zus_rentowa_employer": (0.065, "Składka rentowa pracodawcy"),
    "zus_wypadkowa_employer": (0.0167, "Składka wypadkowa pracodawcy"),

    "fp_rate": (0.01, "Fundusz Pracy"),
    "fs_rate": (0.0145, "Fundusz Solidarnościowy"),
    "fgszp_rate": (0.001, "FGŚP"),

    "health_rate": (0.09, "Składka zdrowotna"),

    "pit_first_rate": (0.12, "PIT - pierwszy próg"),
    "pit_second_rate": (0.32, "PIT - drugi próg"),
    "pit_first_limit_annual": (120000.0, "Roczny limit pierwszego progu PIT"),
    "tax_free_annual": (30000.0, "Roczna kwota wolna od podatku"),
    "tax_reduction_annual": (3600.0, "Roczna kwota zmniejszająca podatek"),

    "uop_kup_standard_monthly": (250.0, "UoP - standardowe koszty uzyskania przychodu"),
    "uop_kup_raised_monthly": (300.0, "UoP - podwyższone koszty uzyskania przychodu"),

    "uz_kup_rate": (0.20, "UZ - koszty uzyskania przychodu"),
    "uod_kup_rate": (0.20, "UoD - koszty uzyskania przychodu"),
    "author_kup_rate": (0.50, "Autorskie koszty uzyskania przychodu"),
    "pit_relief_limit_annual": (85528.0, "Limit zwolnienia z PIT"),

    "ppk_employee_rate": (0.02, "PPK - składka pracownika"),
    "ppk_employer_rate": (0.015, "PPK - składka pracodawcy"),

    "uz_zus_rate": (0.0976, "ZUS emerytalno-rentowe UZ (pełna stawka)"),
    "uz_health_rate": (0.09, "Składka zdrowotna UZ"),
    "uod_tax_rate": (0.12, "Podatek UoD (ryczałt 12%)"),
    
    "life_expectancy_male": (18.5, "Średnie lata emerytury - mężczyźni (GUS)"),
    "life_expectancy_female": (22.0, "Średnie lata emerytury - kobiety (GUS)"),
    "ofe_return_rate": (0.04, "Prognozowana stopa zwrotu OFE"),
    "ppk_return_rate": (0.05, "Prognozowana stopa zwrotu PPK"),
    "default_inflation": (0.03, "Domyślna inflacja"),
    "default_salary_growth": (0.05, "Domyślny wzrost wynagrodzenia"),
    
    "uz_emerytalna_employee": (0.0976, "UZ - składka emerytalna pracownika"),
    "uz_rentowa_employee": (0.015, "UZ - składka rentowa pracownika"),
    "uz_chorobowa_employee": (0.0245, "UZ - składka chorobowa dobrowolna"),
    "uz_emerytalna_employer": (0.0976, "UZ - składka emerytalna zleceniodawcy"),
    "uz_rentowa_employer": (0.065, "UZ - składka rentowa zleceniodawcy"),
    "uz_wypadkowa_employer": (0.0167, "UZ - składka wypadkowa zleceniodawcy"),

    "zus_indexation_rate": (0.03, "Prognozowana roczna waloryzacja kapitału ZUS"),
    "pension_contribution_rate": (0.1952, "Łączna składka emerytalna"),
    "ofe_contribution_rate": (0.0292, "Część składki przekazywana do OFE"),
    "life_expectancy_months_male": (216.0, "Średnie dalsze trwanie życia mężczyzn w miesiącach"),
    "life_expectancy_months_female": (252.0, "Średnie dalsze trwanie życia kobiet w miesiącach"),
}


def get_parameters(as_of: date | None = None) -> dict[str, float]:
    as_of = as_of or date.today()
    params = {}
    for key, (default_val, _) in DEFAULT_PARAMETERS.items():
        record = (
            SystemParameter.query.filter(
                SystemParameter.key == key,
                SystemParameter.valid_from <= as_of,
            )
            .order_by(SystemParameter.valid_from.desc())
            .first()
        )
        params[key] = record.value if record else default_val
    return params
