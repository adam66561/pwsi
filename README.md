# Kalkulator Płacowo-Emerytalny (PWSI)

Aplikacja webowa do obliczania wynagrodzeń (brutto/netto), kosztów pracodawcy oraz symulacji emerytury (ZUS, OFE, PPK)

## Funkcjonalności

### Moduł wynagrodzeń (RF)
- Obliczanie netto z brutto i brutto z netto (UoP, UZ, UoD)
- Koszty pracodawcy (ZUS, FP, FGŚP, PPK)
- Porównanie form zatrudnienia
- Prognoza roczna dochodów

### Moduł emerytalny (RF)
- Symulacja emerytury ZUS, OFE i PPK
- Scenariusze: optymistyczny, bazowy, pesymistyczny
- Wykres trendu przyrostu kapitału
- Konfigurowalne parametry (wiek, inflacja, wzrost wynagrodzenia)

### Raportowanie
- Pasek wynagrodzeń (szczegółowe rozliczenie)
- Eksport PDF (ReportLab)
- Wykresy struktury wypłaty

### Role użytkowników
| Rola | Uprawnienia |
|------|-------------|
| `user` | Kalkulacje, symulacje, historia własnych wariantów |
| `admin` | Zarządzanie kontami, reset haseł, dziennik audytowy |
| `hr_admin` | Edycja parametrów prawnych (stawki ZUS, PIT, progi) |

## Stos technologiczny

- **Backend:** Python 3.11+, Flask, Flask-JWT-Extended
- **Frontend:** HTML/CSS/JS, Bootstrap 5, Chart.js
- **Baza danych:** PostgreSQL (lub SQLite do developmentu)
- **PDF:** ReportLab
- **Bezpieczeństwo:** JWT, bcrypt

## Uruchomienie

### Szybki start (SQLite)

```bash
pip install -r requirements.txt
python run.py
```

Aplikacja dostępna pod adresem: http://localhost:5000

### Z PostgreSQL

```bash
docker compose up -d
cp .env.example .env
# Ustaw DATABASE_URL=postgresql://pwsi:pwsi@localhost:5432/pwsi
pip install -r requirements.txt
python run.py
```

## Konta demonstracyjne

| Login | Hasło | Rola |
|-------|-------|------|
| `user` | `user123` | Użytkownik |
| `admin` | `admin123` | Administrator techniczny |
| `hr_admin` | `hr12345` | Administrator biznesowy (kadry/płace) |

## Struktura projektu

```
pwsi/
├── app/
│   ├── models/          # Modele SQLAlchemy (User, Variant, Parameter, AuditLog)
│   ├── services/        # Logika biznesowa (payroll, pension, PDF, auth)
│   ├── routes/          # Endpointy REST API + strona główna
│   ├── templates/       # Szablon HTML
│   └── static/          # CSS, JavaScript
├── run.py               # Punkt wejścia
├── requirements.txt
└── docker-compose.yml   # PostgreSQL
```

## API (wybrane endpointy)

| Metoda | Endpoint | Opis |
|--------|----------|------|
| POST | `/api/auth/login` | Logowanie (JWT) |
| POST | `/api/calculator/net-from-gross` | Brutto → Netto |
| POST | `/api/calculator/gross-from-net` | Netto → Brutto |
| POST | `/api/pension/simulate` | Symulacja emerytury |
| POST | `/api/reports/payslip/pdf` | Eksport PDF wynagrodzenia |
| GET | `/api/admin/parameters` | Lista parametrów systemowych |
| PUT | `/api/admin/parameters/<id>` | Edycja parametru (hr_admin) |

## Autorzy specyfikacji

Albert Bajera, Jakub Brojek, Maciej Kasprzyk

## Wykonawcy projektu

Adam Kępczyński, Julia Szewczyk, Oliwier Gorzałczyński, Mikołaj Mazurek
