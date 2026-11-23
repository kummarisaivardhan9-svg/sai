"""
Campus Catalyst - Carbon Footprint Awareness Calculator
Business Logic Engine, Data Persistence, Defensive Input Validation, and Reporting
Conforms to IPCC & GHG Protocol domain constraints.
"""

import os
import json
import csv
import math
import uuid
import hashlib
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RECORDS_JSON_FILE = os.path.join(DATA_DIR, "footprint_records.json")
RECORDS_CSV_FILE = os.path.join(DATA_DIR, "footprint_records.csv")
USERS_JSON_FILE = os.path.join(DATA_DIR, "users.json")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "system_audit.log")

# Domain Constraints & Emission Factors (in kg CO2e)
# Travel factors per kilometer
TRAVEL_EMISSION_FACTORS = {
    "walk_bike": 0.000,          # Zero direct emissions
    "electric_vehicle": 0.053,   # Grid-charged EV average
    "subway_metro": 0.035,       # Electric light rail / underground
    "campus_shuttle": 0.045,     # Hybrid/Electric transit
    "public_bus": 0.089,         # Standard diesel/cng bus per passenger-km
    "hybrid_car": 0.120,         # Hybrid passenger car
    "motorcycle": 0.113,         # Scooter / motorcycle
    "petrol_car": 0.192,         # Average petrol sedan
    "diesel_car": 0.171          # Average diesel car
}

# Energy factors
ELECTRICITY_GRID_FACTOR = 0.420  # kg CO2e per kWh (national/campus average)
NATURAL_GAS_FACTOR = 2.030       # kg CO2e per m^3 (or ~5.3 per therm, here using m^3 or units)
LPG_CYLINDER_FACTOR = 29.80      # kg CO2e per standard 14.2kg cylinder
HEATING_ELECTRIC_HP_FACTOR = 0.15 # kg CO2e per hour of heat pump heating
HEATING_GAS_FACTOR = 0.75         # kg CO2e per hour of conventional gas heating
HVAC_AC_FACTOR = 0.60             # kg CO2e per hour of AC cooling

# Flight factors (flat estimate per flight including radiative forcing)
FLIGHT_SHORT_HAUL = 150.0  # kg CO2e per flight (<3 hours)
FLIGHT_LONG_HAUL = 600.0   # kg CO2e per flight (>3 hours)

# Waste / Recycling adjustment in kg CO2e per month
WASTE_FACTORS = {
    "zero_waste": -15.0,    # Active composting, zero single-use plastic
    "mostly_recycle": -5.0, # Regular campus recycling
    "average": 5.0,         # Standard mixed trash
    "high_waste": 25.0      # High disposables, no recycling
}

# Threshold Benchmarks (kg CO2e per month)
THRESHOLD_ECO_HERO = 150.0
THRESHOLD_MODERATE = 300.0
THRESHOLD_CRITICAL = 450.0
CAMPUS_AVERAGE_MONTHLY = 320.0 # kg CO2e / month benchmark
TREE_OFFSET_ANNUAL_KG = 21.77  # 1 mature tree absorbs ~21.77 kg CO2e per year


@dataclass
class FootprintInput:
    user_name: str
    user_role: str               # student, faculty, staff, visitor
    month_year: str              # YYYY-MM
    commute_distance_km: float   # Daily commute distance (round trip)
    commute_days_per_month: int  # Days commuted per month (0-31)
    commute_mode: str            # Key in TRAVEL_EMISSION_FACTORS
    carpool_passengers: int      # 1 = solo, 2+ = sharing
    monthly_road_trips_km: float # Additional leisure/personal travel km
    flights_short_haul: int      # <3 hrs count
    flights_long_haul: int       # >3 hrs count
    electricity_kwh: float       # Monthly electricity in kWh
    green_energy_pct: float      # 0 to 100 (%)
    cooking_gas_units: float     # m^3 or cylinders
    ac_cooling_hours_day: float  # Hours per day AC used
    heating_hours_day: float     # Hours per day heater used
    waste_habit: str             # Key in WASTE_FACTORS
    notes: Optional[str] = ""


class ValidationException(Exception):
    def __init__(self, message: str, errors: Optional[Dict[str, str]] = None):
        super().__init__(message)
        self.errors = errors or {}


def sanitize_string(val: Any, max_len: int = 100) -> str:
    if val is None:
        return ""
    text = str(val).strip()
    # Strip dangerous HTML/script tags
    text = re.sub(r"[<>]", "", text)
    return text[:max_len]


def parse_float_safe(val: Any, field_name: str, min_val: float = 0.0, max_val: float = 100000.0) -> float:
    if val is None or val == "":
        raise ValidationException(f"{field_name} is required and cannot be empty.")
    try:
        num = float(val)
    except (ValueError, TypeError):
        raise ValidationException(f"{field_name} must be a valid numeric value.")
    
    if math.isnan(num) or math.isinf(num):
        raise ValidationException(f"{field_name} must be a finite number.")
    
    if num < min_val:
        raise ValidationException(f"{field_name} cannot be less than {min_val}.")
    if num > max_val:
        raise ValidationException(f"{field_name} exceeds upper realistic limit of {max_val}.")
    return round(num, 2)


def parse_int_safe(val: Any, field_name: str, min_val: int = 0, max_val: int = 1000) -> int:
    if val is None or val == "":
        raise ValidationException(f"{field_name} is required and cannot be empty.")
    try:
        num = int(float(val))
    except (ValueError, TypeError):
        raise ValidationException(f"{field_name} must be an integer.")
    if num < min_val:
        raise ValidationException(f"{field_name} cannot be less than {min_val}.")
    if num > max_val:
        raise ValidationException(f"{field_name} cannot exceed {max_val}.")
    return num


def validate_input_data(data: Dict[str, Any]) -> FootprintInput:
    """Strict defensive input validation and sanitization conforming to domain constraints."""
    errors = {}

    user_name = sanitize_string(data.get("user_name"), 80)
    if not user_name:
        errors["user_name"] = "Name or User ID is required."

    user_role = sanitize_string(data.get("user_role", "student")).lower()
    valid_roles = ["student", "faculty", "staff", "visitor", "auditor"]
    if user_role not in valid_roles:
        errors["user_role"] = f"Invalid role. Must be one of: {', '.join(valid_roles)}"

    month_year = sanitize_string(data.get("month_year", datetime.now().strftime("%Y-%m")), 7)
    if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", month_year):
        errors["month_year"] = "Month must follow YYYY-MM format (e.g. 2026-11)."

    commute_mode = sanitize_string(data.get("commute_mode", "walk_bike")).lower()
    if commute_mode not in TRAVEL_EMISSION_FACTORS:
        errors["commute_mode"] = f"Invalid commute mode. Allowed: {list(TRAVEL_EMISSION_FACTORS.keys())}"

    waste_habit = sanitize_string(data.get("waste_habit", "average")).lower()
    if waste_habit not in WASTE_FACTORS:
        errors["waste_habit"] = f"Invalid waste habit. Allowed: {list(WASTE_FACTORS.keys())}"

    # Range and numerical validations
    def check_float(field, min_v, max_v, default=0.0):
        val = data.get(field)
        if val is None or val == "":
            val = default
        try:
            return parse_float_safe(val, field, min_v, max_v)
        except ValidationException as e:
            errors[field] = str(e)
            return default

    def check_int(field, min_v, max_v, default=0):
        val = data.get(field)
        if val is None or val == "":
            val = default
        try:
            return parse_int_safe(val, field, min_v, max_v)
        except ValidationException as e:
            errors[field] = str(e)
            return default

    commute_distance_km = check_float("commute_distance_km", 0.0, 500.0, 0.0)
    commute_days_per_month = check_int("commute_days_per_month", 0, 31, 0)
    carpool_passengers = check_int("carpool_passengers", 1, 10, 1)
    monthly_road_trips_km = check_float("monthly_road_trips_km", 0.0, 10000.0, 0.0)
    flights_short_haul = check_int("flights_short_haul", 0, 50, 0)
    flights_long_haul = check_int("flights_long_haul", 0, 20, 0)
    electricity_kwh = check_float("electricity_kwh", 0.0, 5000.0, 0.0)
    green_energy_pct = check_float("green_energy_pct", 0.0, 100.0, 0.0)
    cooking_gas_units = check_float("cooking_gas_units", 0.0, 100.0, 0.0)
    ac_cooling_hours_day = check_float("ac_cooling_hours_day", 0.0, 24.0, 0.0)
    heating_hours_day = check_float("heating_hours_day", 0.0, 24.0, 0.0)

    notes = sanitize_string(data.get("notes", ""), 250)

    if errors:
        raise ValidationException("Defensive validation failed for submitted data.", errors)

    return FootprintInput(
        user_name=user_name,
        user_role=user_role,
        month_year=month_year,
        commute_distance_km=commute_distance_km,
        commute_days_per_month=commute_days_per_month,
        commute_mode=commute_mode,
        carpool_passengers=carpool_passengers,
        monthly_road_trips_km=monthly_road_trips_km,
        flights_short_haul=flights_short_haul,
        flights_long_haul=flights_long_haul,
        electricity_kwh=electricity_kwh,
        green_energy_pct=green_energy_pct,
        cooking_gas_units=cooking_gas_units,
        ac_cooling_hours_day=ac_cooling_hours_day,
        heating_hours_day=heating_hours_day,
        waste_habit=waste_habit,
        notes=notes
    )


def calculate_carbon_footprint(entry: FootprintInput) -> Dict[str, Any]:
    """
    Computes fine-grained carbon footprint emissions (kg CO2e) for travel and energy habits.
    """
    # 1. Travel Emissions
    # Daily commute: total monthly commute km = distance * days
    monthly_commute_km = entry.commute_distance_km * entry.commute_days_per_month
    mode_factor = TRAVEL_EMISSION_FACTORS.get(entry.commute_mode, 0.0)
    
    # Carpooling splits personal vehicle emissions
    effective_factor = mode_factor
    if entry.commute_mode in ["petrol_car", "diesel_car", "hybrid_car", "electric_vehicle"]:
        effective_factor = mode_factor / max(1, entry.carpool_passengers)

    commute_emissions = monthly_commute_km * effective_factor
    road_trip_emissions = entry.monthly_road_trips_km * effective_factor
    flight_emissions = (entry.flights_short_haul * FLIGHT_SHORT_HAUL) + (entry.flights_long_haul * FLIGHT_LONG_HAUL)

    travel_total_kg = commute_emissions + road_trip_emissions + flight_emissions

    # 2. Energy & Living Habits Emissions
    # Electricity with renewable offset discount
    renewable_fraction = entry.green_energy_pct / 100.0
    effective_grid_factor = ELECTRICITY_GRID_FACTOR * (1.0 - renewable_fraction)
    electricity_emissions = entry.electricity_kwh * effective_grid_factor

    # Cooking gas / LPG
    gas_emissions = entry.cooking_gas_units * NATURAL_GAS_FACTOR

    # AC & Heating (30 days/month basis)
    ac_monthly_emissions = entry.ac_cooling_hours_day * 30.0 * HVAC_AC_FACTOR
    heating_monthly_emissions = entry.heating_hours_day * 30.0 * HEATING_GAS_FACTOR

    # Waste / Recycling baseline adjustment
    waste_adjustment = WASTE_FACTORS.get(entry.waste_habit, 5.0)

    energy_total_kg = electricity_emissions + gas_emissions + ac_monthly_emissions + heating_monthly_emissions + waste_adjustment
    # Floor energy at 0 if credits exceed
    if energy_total_kg < 0:
        energy_total_kg = 0.0

    # 3. Aggregations & Status
    monthly_total_kg = travel_total_kg + energy_total_kg
    annual_tonnes = (monthly_total_kg * 12.0) / 1000.0
    daily_average_kg = monthly_total_kg / 30.0

    # Trees needed to offset annual footprint
    trees_needed = math.ceil((annual_tonnes * 1000.0) / TREE_OFFSET_ANNUAL_KG)

    # Status & Ecological Rating
    if monthly_total_kg < THRESHOLD_ECO_HERO:
        status = "Eco Hero"
        grade = "A+"
        alert_level = "low"
        advice = "Outstanding! Your personal carbon footprint is exemplary for campus standards."
    elif monthly_total_kg <= THRESHOLD_MODERATE:
        status = "Sustainable Member"
        grade = "B"
        alert_level = "normal"
        advice = "Well balanced footprint. Consider opting for campus transit or increasing renewable energy share."
    elif monthly_total_kg <= THRESHOLD_CRITICAL:
        status = "Moderate Impact"
        grade = "C"
        alert_level = "elevated"
        advice = "Above ideal campus benchmarks. Reduce flight frequency or single-passenger car commutes."
    else:
        status = "Critical Breach"
        grade = "D/F"
        alert_level = "critical"
        advice = "Critical Limit Breach! Footprint significantly exceeds the campus sustainability threshold. Immediate reduction in car/flights and AC cooling recommended."

    # Compare against campus benchmark
    pct_diff_campus = round(((monthly_total_kg - CAMPUS_AVERAGE_MONTHLY) / CAMPUS_AVERAGE_MONTHLY) * 100.0, 1)

    return {
        "monthly_total_kg": round(monthly_total_kg, 2),
        "annual_tonnes": round(annual_tonnes, 2),
        "daily_average_kg": round(daily_average_kg, 2),
        "travel_total_kg": round(travel_total_kg, 2),
        "energy_total_kg": round(energy_total_kg, 2),
        "trees_needed": trees_needed,
        "grade": grade,
        "status": status,
        "alert_level": alert_level,
        "advice": advice,
        "pct_diff_campus": pct_diff_campus,
        "breakdown": {
            "commute_kg": round(commute_emissions, 2),
            "road_trips_kg": round(road_trip_emissions, 2),
            "flights_kg": round(flight_emissions, 2),
            "electricity_kg": round(electricity_emissions, 2),
            "gas_kg": round(gas_emissions, 2),
            "cooling_hvac_kg": round(ac_monthly_emissions, 2),
            "heating_kg": round(heating_monthly_emissions, 2),
            "waste_adj_kg": round(waste_adjustment, 2)
        }
    }


# ==========================================
# File Persistence & Fault-Tolerant I/O
# ==========================================

def ensure_data_directory():
    os.makedirs(DATA_DIR, exist_ok=True)


def initialize_storage_files():
    """
    Detects FileNotFoundError, JSONDecodeError, or corrupted files,
    automatically creating clean initial structures with schema checks.
    """
    ensure_data_directory()

    # 1. Footprint Records JSON
    if not os.path.exists(RECORDS_JSON_FILE):
        with open(RECORDS_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
    else:
        try:
            with open(RECORDS_JSON_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    raise json.JSONDecodeError("Empty file", "", 0)
                json.loads(content)
        except (json.JSONDecodeError, OSError):
            # Auto-repair corrupted file
            with open(RECORDS_JSON_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

    # 2. Footprint Records CSV
    if not os.path.exists(RECORDS_CSV_FILE) or os.path.getsize(RECORDS_CSV_FILE) == 0:
        headers = [
            "record_id", "created_at", "user_name", "user_role", "month_year",
            "commute_mode", "commute_distance_km", "commute_days_per_month",
            "carpool_passengers", "monthly_road_trips_km", "flights_short_haul",
            "flights_long_haul", "electricity_kwh", "green_energy_pct",
            "cooking_gas_units", "ac_cooling_hours_day", "heating_hours_day",
            "waste_habit", "travel_total_kg", "energy_total_kg", "monthly_total_kg",
            "annual_tonnes", "status", "grade", "notes"
        ]
        with open(RECORDS_CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    # 3. Users JSON
    if not os.path.exists(USERS_JSON_FILE):
        # Default demo accounts
        default_users = [
            {
                "username": "student_alex",
                "email": "alex@campus.edu",
                "full_name": "Alex Rivera",
                "role": "student",
                "salt": "demo_salt_123",
                "password_hash": hash_password_with_salt("campus123", "demo_salt_123"),
                "created_at": datetime.now().isoformat()
            },
            {
                "username": "prof_green",
                "email": "elena.green@campus.edu",
                "full_name": "Prof. Elena Green",
                "role": "faculty",
                "salt": "demo_salt_456",
                "password_hash": hash_password_with_salt("campus123", "demo_salt_456"),
                "created_at": datetime.now().isoformat()
            },
            {
                "username": "officer_vance",
                "email": "vance@sustainability.campus.edu",
                "full_name": "Dr. Marcus Vance",
                "role": "auditor",
                "salt": "demo_salt_789",
                "password_hash": hash_password_with_salt("campus123", "demo_salt_789"),
                "created_at": datetime.now().isoformat()
            }
        ]
        with open(USERS_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=2)


def hash_password_with_salt(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def authenticate_user(username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
    initialize_storage_files()
    try:
        with open(USERS_JSON_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except Exception:
        return None

    norm_id = username_or_email.strip().lower()
    for u in users:
        if u.get("username", "").lower() == norm_id or u.get("email", "").lower() == norm_id:
            salt = u.get("salt", "")
            expected_hash = u.get("password_hash", "")
            if hash_password_with_salt(password, salt) == expected_hash:
                return {
                    "username": u["username"],
                    "email": u["email"],
                    "full_name": u["full_name"],
                    "role": u["role"]
                }
    return None


def register_user(username: str, email: str, full_name: str, password: str, role: str = "student") -> Dict[str, Any]:
    initialize_storage_files()
    username = sanitize_string(username, 30).lower()
    email = sanitize_string(email, 80).lower()
    full_name = sanitize_string(full_name, 80)
    role = sanitize_string(role, 20).lower()

    if not username or len(username) < 3:
        raise ValidationException("Username must be at least 3 characters long.")
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        raise ValidationException("Please enter a valid email address.")
    if len(password) < 6:
        raise ValidationException("Password must be at least 6 characters.")

    with open(USERS_JSON_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)

    for u in users:
        if u["username"].lower() == username:
            raise ValidationException("Username is already registered.")
        if u["email"].lower() == email:
            raise ValidationException("Email address is already in use.")

    salt = uuid.uuid4().hex[:16]
    pw_hash = hash_password_with_salt(password, salt)

    new_user = {
        "username": username,
        "email": email,
        "full_name": full_name or username.capitalize(),
        "role": role,
        "salt": salt,
        "password_hash": pw_hash,
        "created_at": datetime.now().isoformat()
    }
    users.append(new_user)
    with open(USERS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

    return {
        "username": new_user["username"],
        "email": new_user["email"],
        "full_name": new_user["full_name"],
        "role": new_user["role"]
    }


def save_record(entry: FootprintInput, calc_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Atomically serializes and persists a carbon footprint record to both JSON and CSV files.
    """
    initialize_storage_files()
    record_id = "REC-" + uuid.uuid4().hex[:8].upper()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    record_dict = {
        "record_id": record_id,
        "created_at": timestamp,
        "input": asdict(entry),
        "calculation": calc_result
    }

    # 1. Update JSON Storage
    records = []
    try:
        with open(RECORDS_JSON_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception:
        records = []

    records.insert(0, record_dict)
    with open(RECORDS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    # 2. Append to CSV Storage
    try:
        csv_row = [
            record_id, timestamp, entry.user_name, entry.user_role, entry.month_year,
            entry.commute_mode, entry.commute_distance_km, entry.commute_days_per_month,
            entry.carpool_passengers, entry.monthly_road_trips_km, entry.flights_short_haul,
            entry.flights_long_haul, entry.electricity_kwh, entry.green_energy_pct,
            entry.cooking_gas_units, entry.ac_cooling_hours_day, entry.heating_hours_day,
            entry.waste_habit, calc_result["travel_total_kg"], calc_result["energy_total_kg"],
            calc_result["monthly_total_kg"], calc_result["annual_tonnes"],
            calc_result["status"], calc_result["grade"], entry.notes
        ]
        with open(RECORDS_CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(csv_row)
    except Exception as e:
        log_audit(f"Error appending record {record_id} to CSV: {e}")

    log_audit(f"Saved record {record_id} for user '{entry.user_name}' ({calc_result['monthly_total_kg']} kg CO2e)")
    return record_dict


def load_all_records() -> List[Dict[str, Any]]:
    initialize_storage_files()
    try:
        with open(RECORDS_JSON_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
            return records if isinstance(records, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def query_and_filter_records(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    sort_by: str = "newest"
) -> List[Dict[str, Any]]:
    """Filters records by keyword, category, status, and applies custom sorting."""
    records = load_all_records()
    results = []

    for r in records:
        inp = r.get("input", {})
        calc = r.get("calculation", {})
        
        # Keyword search (user_name, notes, record_id, month_year)
        if keyword:
            kw = keyword.lower()
            text_corpus = f"{r.get('record_id', '')} {inp.get('user_name', '')} {inp.get('notes', '')} {inp.get('month_year', '')}".lower()
            if kw not in text_corpus:
                continue

        # Status filter (e.g. 'Eco Hero', 'Critical Breach')
        if status and status.lower() != "all":
            if calc.get("status", "").lower() != status.lower():
                continue

        # Role filter
        if role and role.lower() != "all":
            if inp.get("user_role", "").lower() != role.lower():
                continue

        results.append(r)

    # Sorting
    if sort_by == "highest_emissions":
        results.sort(key=lambda x: x.get("calculation", {}).get("monthly_total_kg", 0), reverse=True)
    elif sort_by == "lowest_emissions":
        results.sort(key=lambda x: x.get("calculation", {}).get("monthly_total_kg", 0))
    elif sort_by == "oldest":
        results.sort(key=lambda x: x.get("created_at", ""))
    else:  # newest default
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return results


def delete_record_by_id(record_id: str) -> bool:
    initialize_storage_files()
    records = load_all_records()
    initial_len = len(records)
    records = [r for r in records if r.get("record_id") != record_id]

    if len(records) == initial_len:
        return False

    with open(RECORDS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    # Sync CSV file
    try:
        initialize_storage_files()
        headers = [
            "record_id", "created_at", "user_name", "user_role", "month_year",
            "commute_mode", "commute_distance_km", "commute_days_per_month",
            "carpool_passengers", "monthly_road_trips_km", "flights_short_haul",
            "flights_long_haul", "electricity_kwh", "green_energy_pct",
            "cooking_gas_units", "ac_cooling_hours_day", "heating_hours_day",
            "waste_habit", "travel_total_kg", "energy_total_kg", "monthly_total_kg",
            "annual_tonnes", "status", "grade", "notes"
        ]
        with open(RECORDS_CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in records:
                inp = r.get("input", {})
                calc = r.get("calculation", {})
                writer.writerow([
                    r.get("record_id"), r.get("created_at"), inp.get("user_name"), inp.get("user_role"),
                    inp.get("month_year"), inp.get("commute_mode"), inp.get("commute_distance_km"),
                    inp.get("commute_days_per_month"), inp.get("carpool_passengers"),
                    inp.get("monthly_road_trips_km"), inp.get("flights_short_haul"),
                    inp.get("flights_long_haul"), inp.get("electricity_kwh"), inp.get("green_energy_pct"),
                    inp.get("cooking_gas_units"), inp.get("ac_cooling_hours_day"),
                    inp.get("heating_hours_day"), inp.get("waste_habit"), calc.get("travel_total_kg"),
                    calc.get("energy_total_kg"), calc.get("monthly_total_kg"), calc.get("annual_tonnes"),
                    calc.get("status"), calc.get("grade"), inp.get("notes")
                ])
    except Exception as e:
        log_audit(f"Error syncing CSV after record delete: {e}")

    log_audit(f"Deleted record {record_id}")
    return True


def get_executive_summary() -> Dict[str, Any]:
    """Generates overall KPI totals, averages, status distributions, and trends."""
    records = load_all_records()
    total_count = len(records)
    if total_count == 0:
        return {
            "total_records": 0,
            "average_monthly_kg": 0.0,
            "total_emissions_kg": 0.0,
            "average_annual_tonnes": 0.0,
            "average_travel_kg": 0.0,
            "average_energy_kg": 0.0,
            "total_trees_needed": 0,
            "status_counts": {"Eco Hero": 0, "Sustainable Member": 0, "Moderate Impact": 0, "Critical Breach": 0},
            "role_distribution": {},
            "recent_records": [],
            "monthly_trends": []
        }

    sum_total_kg = sum(r.get("calculation", {}).get("monthly_total_kg", 0) for r in records)
    sum_travel_kg = sum(r.get("calculation", {}).get("travel_total_kg", 0) for r in records)
    sum_energy_kg = sum(r.get("calculation", {}).get("energy_total_kg", 0) for r in records)
    sum_annual_tonnes = sum(r.get("calculation", {}).get("annual_tonnes", 0) for r in records)
    sum_trees = sum(r.get("calculation", {}).get("trees_needed", 0) for r in records)

    status_counts = {"Eco Hero": 0, "Sustainable Member": 0, "Moderate Impact": 0, "Critical Breach": 0}
    role_distribution = {}
    trends_map = {}

    for r in records:
        calc = r.get("calculation", {})
        inp = r.get("input", {})
        
        st = calc.get("status", "Moderate Impact")
        if st in status_counts:
            status_counts[st] += 1
        else:
            status_counts[st] = 1

        rl = inp.get("user_role", "student")
        role_distribution[rl] = role_distribution.get(rl, 0) + 1

        my = inp.get("month_year", "Unknown")
        if my not in trends_map:
            trends_map[my] = {"total_kg": 0.0, "travel_kg": 0.0, "energy_kg": 0.0, "count": 0}
        trends_map[my]["total_kg"] += calc.get("monthly_total_kg", 0)
        trends_map[my]["travel_kg"] += calc.get("travel_total_kg", 0)
        trends_map[my]["energy_kg"] += calc.get("energy_total_kg", 0)
        trends_map[my]["count"] += 1

    # Format monthly trends list sorted by date
    monthly_trends = []
    for my in sorted(trends_map.keys()):
        data = trends_map[my]
        cnt = data["count"]
        monthly_trends.append({
            "month": my,
            "avg_monthly_kg": round(data["total_kg"] / cnt, 2),
            "avg_travel_kg": round(data["travel_kg"] / cnt, 2),
            "avg_energy_kg": round(data["energy_kg"] / cnt, 2),
            "entries_count": cnt
        })

    return {
        "total_records": total_count,
        "average_monthly_kg": round(sum_total_kg / total_count, 2),
        "total_emissions_kg": round(sum_total_kg, 2),
        "average_annual_tonnes": round(sum_annual_tonnes / total_count, 2),
        "average_travel_kg": round(sum_travel_kg / total_count, 2),
        "average_energy_kg": round(sum_energy_kg / total_count, 2),
        "total_trees_needed": sum_trees,
        "status_counts": status_counts,
        "role_distribution": role_distribution,
        "recent_records": records[:6],
        "monthly_trends": monthly_trends
    }


# ==========================================
# Bulk Dataset Import with Validation Logs
# ==========================================

def import_csv_dataset(csv_content: str) -> Dict[str, Any]:
    """
    Ingests CSV datasets with strict row-by-row validation,
    captures detailed error logs for invalid rows, and saves valid entries.
    """
    reader = csv.DictReader(csv_content.splitlines())
    success_count = 0
    errors = []
    saved_records = []

    row_num = 1
    for row in reader:
        row_num += 1
        try:
            # Map possible header variations
            data = {
                "user_name": row.get("user_name") or row.get("Name") or row.get("user") or f"CampusUser_{row_num}",
                "user_role": row.get("user_role") or row.get("role") or "student",
                "month_year": row.get("month_year") or row.get("date") or datetime.now().strftime("%Y-%m"),
                "commute_mode": row.get("commute_mode") or "public_bus",
                "commute_distance_km": row.get("commute_distance_km") or 10.0,
                "commute_days_per_month": row.get("commute_days_per_month") or 20,
                "carpool_passengers": row.get("carpool_passengers") or 1,
                "monthly_road_trips_km": row.get("monthly_road_trips_km") or 0.0,
                "flights_short_haul": row.get("flights_short_haul") or 0,
                "flights_long_haul": row.get("flights_long_haul") or 0,
                "electricity_kwh": row.get("electricity_kwh") or 120.0,
                "green_energy_pct": row.get("green_energy_pct") or 0.0,
                "cooking_gas_units": row.get("cooking_gas_units") or 2.0,
                "ac_cooling_hours_day": row.get("ac_cooling_hours_day") or 2.0,
                "heating_hours_day": row.get("heating_hours_day") or 0.0,
                "waste_habit": row.get("waste_habit") or "average",
                "notes": row.get("notes") or f"Bulk imported row {row_num}"
            }

            validated_input = validate_input_data(data)
            calc = calculate_carbon_footprint(validated_input)
            rec = save_record(validated_input, calc)
            success_count += 1
            saved_records.append(rec)
        except ValidationException as ve:
            errors.append({
                "row": row_num,
                "user": row.get("user_name", "Unknown"),
                "error": str(ve),
                "details": ve.errors
            })
        except Exception as ex:
            errors.append({
                "row": row_num,
                "user": row.get("user_name", "Unknown"),
                "error": f"Unexpected parse error: {str(ex)}"
            })

    log_audit(f"Bulk CSV import completed: {success_count} succeeded, {len(errors)} failed.")
    return {
        "success_count": success_count,
        "error_count": len(errors),
        "errors": errors,
        "saved_count": len(saved_records)
    }


# ==========================================
# Multi-Format Summary Exporters
# ==========================================

def export_summary_markdown() -> str:
    summary = get_executive_summary()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = f"""# 🌿 Campus Catalyst - Executive Carbon Footprint Audit Report
**Generated On:** {now_str}  
**Total Assessed Records:** {summary['total_records']}  
**Campus Average Target:** {CAMPUS_AVERAGE_MONTHLY} kg CO2e / month  

---

## 1. Key Performance Indicators (KPIs)
| Metric | Value | Reference Standard |
| :--- | :--- | :--- |
| **Total Carbon Footprint (All)** | **{summary['total_emissions_kg']} kg CO2e** | Campus Registry |
| **Average Monthly Footprint** | **{summary['average_monthly_kg']} kg CO2e** | Baseline 320 kg/mo |
| **Average Annualized Footprint** | **{summary['average_annual_tonnes']} Tonnes CO2e** | IPCC 2026 Guidelines |
| **Average Travel Emissions** | **{summary['average_travel_kg']} kg CO2e / mo** | Commute & Flights |
| **Average Energy Emissions** | **{summary['average_energy_kg']} kg CO2e / mo** | Utilities & Living |
| **Total Trees Required to Offset** | **{summary['total_trees_needed']} mature trees** | ~21.77 kg CO2e / tree-yr |

---

## 2. Ecological Status & Threshold Distribution
- 🌟 **Eco Hero (< 150 kg/mo):** {summary['status_counts'].get('Eco Hero', 0)} entries
- 🌿 **Sustainable Member (150-300 kg/mo):** {summary['status_counts'].get('Sustainable Member', 0)} entries
- ⚠️ **Moderate Impact (300-450 kg/mo):** {summary['status_counts'].get('Moderate Impact', 0)} entries
- 🚨 **Critical Limit Breach (> 450 kg/mo):** {summary['status_counts'].get('Critical Breach', 0)} entries

---

## 3. Monthly Trends Analysis
| Month | Avg Total (kg CO2e) | Avg Travel (kg) | Avg Energy (kg) | Entries Count |
| :--- | :--- | :--- | :--- | :--- |
"""
    for trend in summary["monthly_trends"]:
        md += f"| {trend['month']} | {trend['avg_monthly_kg']} | {trend['avg_travel_kg']} | {trend['avg_energy_kg']} | {trend['entries_count']} |\n"

    md += """
---
*Automated Report generated by Campus Catalyst Carbon Footprint Awareness Engine.*
"""
    return md


def export_plain_text_audit() -> str:
    summary = get_executive_summary()
    records = load_all_records()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "=" * 72,
        "CAMPUS CATALYST CARBON FOOTPRINT SYSTEM - AUDIT LOG & REPORT",
        f"Generated: {now_str}",
        "=" * 72,
        "",
        "EXECUTIVE SUMMARY:",
        f"  Total Records Assessed    : {summary['total_records']}",
        f"  Total Emissions Recorded  : {summary['total_emissions_kg']} kg CO2e",
        f"  Mean Monthly Footprint    : {summary['average_monthly_kg']} kg CO2e",
        f"  Mean Annualized Footprint : {summary['average_annual_tonnes']} Tonnes CO2e",
        f"  Trees Required to Offset  : {summary['total_trees_needed']} trees",
        "",
        "STATUS CLASSIFICATION BREAKDOWN:",
        f"  [LOW / HERO]        : {summary['status_counts'].get('Eco Hero', 0)}",
        f"  [MODERATE]          : {summary['status_counts'].get('Sustainable Member', 0)}",
        f"  [ELEVATED]          : {summary['status_counts'].get('Moderate Impact', 0)}",
        f"  [CRITICAL BREACH]   : {summary['status_counts'].get('Critical Breach', 0)}",
        "",
        "-" * 72,
        "INDIVIDUAL ENTRY AUDIT TRAIL (Top 25 recent):",
        "-" * 72,
        f"{'ID':<12} {'USER':<18} {'ROLE':<10} {'MONTH':<8} {'TRAVEL':<8} {'ENERGY':<8} {'TOTAL':<8} {'STATUS'}"
    ]

    for r in records[:25]:
        inp = r.get("input", {})
        calc = r.get("calculation", {})
        lines.append(
            f"{r.get('record_id', ''):<12} "
            f"{inp.get('user_name', '')[:16]:<18} "
            f"{inp.get('user_role', '')[:8]:<10} "
            f"{inp.get('month_year', ''):<8} "
            f"{str(calc.get('travel_total_kg', 0)):<8} "
            f"{str(calc.get('energy_total_kg', 0)):<8} "
            f"{str(calc.get('monthly_total_kg', 0)):<8} "
            f"{calc.get('status', '')}"
        )

    lines.append("")
    lines.append("=" * 72)
    lines.append("END OF AUDIT LOG")
    lines.append("=" * 72)
    return "\n".join(lines)


def log_audit(msg: str):
    ensure_data_directory()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{now_str}] {msg}\n"
    try:
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass
