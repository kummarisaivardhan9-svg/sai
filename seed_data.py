"""
Campus Catalyst - Dataset Seeder
Generates 50 varied, realistic test cases (normal entries, boundary values, edge conditions)
representing campus stakeholders (students, faculty, lab staff, commuters).
"""

import os
import csv
import json
from datetime import datetime
from business_logic import (
    initialize_storage_files, validate_input_data, calculate_carbon_footprint,
    save_record, DATA_DIR, RECORDS_JSON_FILE
)

SAMPLE_CSV_PATH = os.path.join(DATA_DIR, "sample_dataset_50.csv")

REALISTIC_PROFILES = [
    # Normal Student Cases (Dorm, walking/bus, low/moderate emissions)
    {"user_name": "Alex Rivera", "user_role": "student", "month_year": "2026-11", "commute_distance_km": 2.0, "commute_days_per_month": 22, "commute_mode": "walk_bike", "carpool_passengers": 1, "monthly_road_trips_km": 0.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 65.0, "green_energy_pct": 50.0, "cooking_gas_units": 0.0, "ac_cooling_hours_day": 1.0, "heating_hours_day": 0.0, "waste_habit": "zero_waste", "notes": "On-campus dorm resident, bikes everywhere"},
    {"user_name": "Maya Lin", "user_role": "student", "month_year": "2026-11", "commute_distance_km": 6.5, "commute_days_per_month": 20, "commute_mode": "campus_shuttle", "carpool_passengers": 1, "monthly_road_trips_km": 25.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 85.0, "green_energy_pct": 20.0, "cooking_gas_units": 1.5, "ac_cooling_hours_day": 2.0, "heating_hours_day": 1.0, "waste_habit": "mostly_recycle", "notes": "Shuttle commuter, off-campus shared flat"},
    {"user_name": "Liam Connor", "user_role": "student", "month_year": "2026-11", "commute_distance_km": 12.0, "commute_days_per_month": 18, "commute_mode": "subway_metro", "carpool_passengers": 1, "monthly_road_trips_km": 40.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 95.0, "green_energy_pct": 10.0, "cooking_gas_units": 2.0, "ac_cooling_hours_day": 3.0, "heating_hours_day": 1.5, "waste_habit": "average", "notes": "Commuter via metro"},
    {"user_name": "Zara Patel", "user_role": "student", "month_year": "2026-10", "commute_distance_km": 4.0, "commute_days_per_month": 24, "commute_mode": "public_bus", "carpool_passengers": 1, "monthly_road_trips_km": 15.0, "flights_short_haul": 1, "flights_long_haul": 0, "electricity_kwh": 70.0, "green_energy_pct": 30.0, "cooking_gas_units": 1.0, "ac_cooling_hours_day": 1.5, "heating_hours_day": 0.0, "waste_habit": "mostly_recycle", "notes": "Attended weekend hackathon in adjacent city"},
    {"user_name": "Ethan Hunt", "user_role": "student", "month_year": "2026-11", "commute_distance_km": 8.0, "commute_days_per_month": 16, "commute_mode": "motorcycle", "carpool_passengers": 1, "monthly_road_trips_km": 60.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 110.0, "green_energy_pct": 0.0, "cooking_gas_units": 3.0, "ac_cooling_hours_day": 4.0, "heating_hours_day": 0.0, "waste_habit": "average", "notes": "Scooter commuter"},
    {"user_name": "Chloe Bennett", "user_role": "student", "month_year": "2026-09", "commute_distance_km": 1.5, "commute_days_per_month": 26, "commute_mode": "walk_bike", "carpool_passengers": 1, "monthly_road_trips_km": 0.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 45.0, "green_energy_pct": 80.0, "cooking_gas_units": 0.0, "ac_cooling_hours_day": 0.5, "heating_hours_day": 0.0, "waste_habit": "zero_waste", "notes": "Eco-club volunteer president"},
    {"user_name": "Noah Kim", "user_role": "student", "month_year": "2026-10", "commute_distance_km": 15.0, "commute_days_per_month": 20, "commute_mode": "hybrid_car", "carpool_passengers": 3, "monthly_road_trips_km": 50.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 120.0, "green_energy_pct": 25.0, "cooking_gas_units": 2.5, "ac_cooling_hours_day": 3.0, "heating_hours_day": 1.0, "waste_habit": "mostly_recycle", "notes": "Student carpool of 3 passengers"},
    {"user_name": "Sophia Rossi", "user_role": "student", "month_year": "2026-11", "commute_distance_km": 5.0, "commute_days_per_month": 22, "commute_mode": "electric_vehicle", "carpool_passengers": 2, "monthly_road_trips_km": 30.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 140.0, "green_energy_pct": 40.0, "cooking_gas_units": 1.0, "ac_cooling_hours_day": 2.0, "heating_hours_day": 1.0, "waste_habit": "mostly_recycle", "notes": "Drives small shared EV"},
    {"user_name": "David O'Connor", "user_role": "student", "month_year": "2026-10", "commute_distance_km": 18.0, "commute_days_per_month": 21, "commute_mode": "petrol_car", "carpool_passengers": 1, "monthly_road_trips_km": 120.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 180.0, "green_energy_pct": 0.0, "cooking_gas_units": 3.5, "ac_cooling_hours_day": 5.0, "heating_hours_day": 2.0, "waste_habit": "high_waste", "notes": "Solo driver, suburban commuter"},
    {"user_name": "Amina Al-Mansoor", "user_role": "student", "month_year": "2026-11", "commute_distance_km": 3.0, "commute_days_per_month": 25, "commute_mode": "walk_bike", "carpool_passengers": 1, "monthly_road_trips_km": 10.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 60.0, "green_energy_pct": 60.0, "cooking_gas_units": 0.5, "ac_cooling_hours_day": 1.0, "heating_hours_day": 0.5, "waste_habit": "zero_waste", "notes": "Campus residence assistant"},

    # Faculty & Researchers (Medium/Higher emissions, travel & flights)
    {"user_name": "Prof. Elena Green", "user_role": "faculty", "month_year": "2026-11", "commute_distance_km": 14.0, "commute_days_per_month": 18, "commute_mode": "electric_vehicle", "carpool_passengers": 1, "monthly_road_trips_km": 80.0, "flights_short_haul": 1, "flights_long_haul": 0, "electricity_kwh": 220.0, "green_energy_pct": 50.0, "cooking_gas_units": 4.0, "ac_cooling_hours_day": 4.0, "heating_hours_day": 2.0, "waste_habit": "mostly_recycle", "notes": "Environmental sciences department chair"},
    {"user_name": "Dr. Marcus Vance", "user_role": "auditor", "month_year": "2026-11", "commute_distance_km": 8.0, "commute_days_per_month": 20, "commute_mode": "subway_metro", "carpool_passengers": 1, "monthly_road_trips_km": 40.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 150.0, "green_energy_pct": 75.0, "cooking_gas_units": 2.0, "ac_cooling_hours_day": 2.0, "heating_hours_day": 1.0, "waste_habit": "zero_waste", "notes": "Campus Sustainability Officer"},
    {"user_name": "Dr. Robert Thorne", "user_role": "faculty", "month_year": "2026-10", "commute_distance_km": 28.0, "commute_days_per_month": 20, "commute_mode": "petrol_car", "carpool_passengers": 1, "monthly_road_trips_km": 200.0, "flights_short_haul": 2, "flights_long_haul": 1, "electricity_kwh": 380.0, "green_energy_pct": 0.0, "cooking_gas_units": 6.0, "ac_cooling_hours_day": 7.0, "heating_hours_day": 3.0, "waste_habit": "average", "notes": "Attended international IEEE symposium in Munich"},
    {"user_name": "Prof. Ananya Sen", "user_role": "faculty", "month_year": "2026-11", "commute_distance_km": 10.0, "commute_days_per_month": 16, "commute_mode": "hybrid_car", "carpool_passengers": 2, "monthly_road_trips_km": 60.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 190.0, "green_energy_pct": 30.0, "cooking_gas_units": 3.0, "ac_cooling_hours_day": 3.0, "heating_hours_day": 2.0, "waste_habit": "mostly_recycle", "notes": "Shared commute with faculty peer"},
    {"user_name": "Dr. Samuel Jackson", "user_role": "faculty", "month_year": "2026-09", "commute_distance_km": 32.0, "commute_days_per_month": 14, "commute_mode": "diesel_car", "carpool_passengers": 1, "monthly_road_trips_km": 150.0, "flights_short_haul": 1, "flights_long_haul": 0, "electricity_kwh": 310.0, "green_energy_pct": 10.0, "cooking_gas_units": 5.0, "ac_cooling_hours_day": 5.0, "heating_hours_day": 2.5, "waste_habit": "average", "notes": "Physics laboratory coordinator"},
    {"user_name": "Prof. Clara Wu", "user_role": "faculty", "month_year": "2026-10", "commute_distance_km": 5.0, "commute_days_per_month": 18, "commute_mode": "walk_bike", "carpool_passengers": 1, "monthly_road_trips_km": 30.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 130.0, "green_energy_pct": 90.0, "cooking_gas_units": 1.5, "ac_cooling_hours_day": 2.0, "heating_hours_day": 1.0, "waste_habit": "zero_waste", "notes": "Solar-powered residence owner"},
    {"user_name": "Dr. Kenneth Cole", "user_role": "faculty", "month_year": "2026-11", "commute_distance_km": 40.0, "commute_days_per_month": 19, "commute_mode": "petrol_car", "carpool_passengers": 1, "monthly_road_trips_km": 300.0, "flights_short_haul": 2, "flights_long_haul": 1, "electricity_kwh": 420.0, "green_energy_pct": 0.0, "cooking_gas_units": 7.0, "ac_cooling_hours_day": 8.0, "heating_hours_day": 4.0, "waste_habit": "high_waste", "notes": "Heavy commuter with intercity lab visits"},

    # Campus Staff & Facilities Operations
    {"user_name": "George Miller", "user_role": "staff", "month_year": "2026-11", "commute_distance_km": 11.0, "commute_days_per_month": 22, "commute_mode": "public_bus", "carpool_passengers": 1, "monthly_road_trips_km": 40.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 160.0, "green_energy_pct": 15.0, "cooking_gas_units": 3.0, "ac_cooling_hours_day": 3.0, "heating_hours_day": 1.5, "waste_habit": "average", "notes": "Campus facilities manager"},
    {"user_name": "Brenda Scott", "user_role": "staff", "month_year": "2026-10", "commute_distance_km": 7.0, "commute_days_per_month": 23, "commute_mode": "campus_shuttle", "carpool_passengers": 1, "monthly_road_trips_km": 20.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 140.0, "green_energy_pct": 20.0, "cooking_gas_units": 2.5, "ac_cooling_hours_day": 2.5, "heating_hours_day": 1.0, "waste_habit": "mostly_recycle", "notes": "Student registrar office"},
    {"user_name": "Hassan Raza", "user_role": "staff", "month_year": "2026-11", "commute_distance_km": 16.0, "commute_days_per_month": 20, "commute_mode": "motorcycle", "carpool_passengers": 1, "monthly_road_trips_km": 50.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 175.0, "green_energy_pct": 0.0, "cooking_gas_units": 3.5, "ac_cooling_hours_day": 4.0, "heating_hours_day": 1.0, "waste_habit": "average", "notes": "IT support lead technician"},
    {"user_name": "Maria Hernandez", "user_role": "staff", "month_year": "2026-09", "commute_distance_km": 9.0, "commute_days_per_month": 24, "commute_mode": "subway_metro", "carpool_passengers": 1, "monthly_road_trips_km": 30.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 130.0, "green_energy_pct": 35.0, "cooking_gas_units": 2.0, "ac_cooling_hours_day": 2.0, "heating_hours_day": 1.0, "waste_habit": "mostly_recycle", "notes": "Library senior cataloger"},

    # Boundary & Edge Test Cases (as explicitly required by Section 7 & 8)
    # Edge 1: Zero emissions boundary (extreme green lifestyle)
    {"user_name": "Greta Eco-Champion", "user_role": "student", "month_year": "2026-11", "commute_distance_km": 0.0, "commute_days_per_month": 0, "commute_mode": "walk_bike", "carpool_passengers": 1, "monthly_road_trips_km": 0.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 10.0, "green_energy_pct": 100.0, "cooking_gas_units": 0.0, "ac_cooling_hours_day": 0.0, "heating_hours_day": 0.0, "waste_habit": "zero_waste", "notes": "[EDGE CASE] 100% renewable off-grid, walks everywhere, near-zero net"},
    # Edge 2: Heavy emissions boundary (upper threshold breach)
    {"user_name": "Victor High-Carbon", "user_role": "visitor", "month_year": "2026-11", "commute_distance_km": 60.0, "commute_days_per_month": 28, "commute_mode": "petrol_car", "carpool_passengers": 1, "monthly_road_trips_km": 800.0, "flights_short_haul": 4, "flights_long_haul": 2, "electricity_kwh": 850.0, "green_energy_pct": 0.0, "cooking_gas_units": 12.0, "ac_cooling_hours_day": 14.0, "heating_hours_day": 6.0, "waste_habit": "high_waste", "notes": "[EDGE CASE] Extreme breach testing high threshold warnings"},
    # Edge 3: Maximum Carpooling boundary
    {"user_name": "Carpool Squad Delta", "user_role": "student", "month_year": "2026-11", "commute_distance_km": 25.0, "commute_days_per_month": 22, "commute_mode": "petrol_car", "carpool_passengers": 5, "monthly_road_trips_km": 100.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 120.0, "green_energy_pct": 20.0, "cooking_gas_units": 2.0, "ac_cooling_hours_day": 3.0, "heating_hours_day": 1.0, "waste_habit": "average", "notes": "[BOUNDARY CASE] 5-passenger carpool split verification"},
    # Edge 4: Minimum days (0 days commute, all remote)
    {"user_name": "Online Scholar Kai", "user_role": "student", "month_year": "2026-11", "commute_distance_km": 0.0, "commute_days_per_month": 0, "commute_mode": "walk_bike", "carpool_passengers": 1, "monthly_road_trips_km": 0.0, "flights_short_haul": 0, "flights_long_haul": 0, "electricity_kwh": 110.0, "green_energy_pct": 10.0, "cooking_gas_units": 1.5, "ac_cooling_hours_day": 3.0, "heating_hours_day": 1.0, "waste_habit": "average", "notes": "[BOUNDARY CASE] Fully remote student with zero commute km"},
    # Edge 5: High flight traveler
    {"user_name": "Visiting Fellow Hans", "user_role": "visitor", "month_year": "2026-10", "commute_distance_km": 5.0, "commute_days_per_month": 10, "commute_mode": "campus_shuttle", "carpool_passengers": 1, "monthly_road_trips_km": 20.0, "flights_short_haul": 3, "flights_long_haul": 1, "electricity_kwh": 90.0, "green_energy_pct": 10.0, "cooking_gas_units": 1.0, "ac_cooling_hours_day": 2.0, "heating_hours_day": 1.0, "waste_habit": "average", "notes": "[EDGE CASE] Visiting international scholar flight surge"},
]

# Additional generated entries to bring total to 50
FIRST_NAMES = ["Oliver", "Emma", "Lucas", "Mia", "Alexander", "Isabella", "Benjamin", "Charlotte", "Daniel", "Amelia", "Henry", "Harper", "Sebastian", "Evelyn", "Jack", "Abigail", "Julian", "Emily", "Levi", "Ella", "Owen", "Avery", "Samuel", "Sofia", "Ryan", "Aria", "Nathan", "Scarlett", "Isaac"]
LAST_NAMES = ["Chen", "Murphy", "Singh", "Garcia", "Kim", "Tanaka", "Muller", "Dubois", "Santos", "Johansson", "Kowalski", "Yilmaz", "Novak", "Popov", "Larsson", "Alvarez", "Nielsen", "Wong", "Adler", "Bauer", "Fischer", "Weber", "Meyer", "Schulz", "Becker", "Hoffmann", "Schafer", "Koch", "Bauer"]
MODES = ["walk_bike", "campus_shuttle", "subway_metro", "public_bus", "electric_vehicle", "hybrid_car", "petrol_car", "diesel_car", "motorcycle"]

def generate_50_dataset():
    initialize_storage_files()
    records = list(REALISTIC_PROFILES) # 21 profile cases

    # Add 29 more to reach exactly 50 varied records
    import random
    random.seed(42) # Deterministic seed for reproducible testing

    for i in range(29):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[i % len(LAST_NAMES)]
        role = random.choice(["student", "student", "student", "faculty", "staff"])
        mode = random.choice(MODES)
        dist = round(random.uniform(1.0, 35.0), 1) if mode != "walk_bike" else round(random.uniform(0.5, 4.0), 1)
        days = random.randint(12, 26)
        passengers = random.randint(1, 4) if "car" in mode else 1
        road_trips = round(random.uniform(0.0, 150.0), 1)
        flights_sh = 1 if random.random() < 0.20 else 0
        flights_lh = 1 if random.random() < 0.08 else 0
        elec = round(random.uniform(50.0, 260.0), 1)
        green = round(random.choice([0.0, 15.0, 30.0, 50.0, 75.0, 100.0]), 1)
        gas = round(random.uniform(0.0, 4.5), 1)
        ac = round(random.uniform(0.0, 6.0), 1)
        heat = round(random.uniform(0.0, 3.0), 1)
        waste = random.choice(["zero_waste", "mostly_recycle", "average", "high_waste"])
        month = random.choice(["2026-08", "2026-09", "2026-10", "2026-11"])

        rec = {
            "user_name": f"{first} {last}",
            "user_role": role,
            "month_year": month,
            "commute_distance_km": dist,
            "commute_days_per_month": days,
            "commute_mode": mode,
            "carpool_passengers": passengers,
            "monthly_road_trips_km": road_trips,
            "flights_short_haul": flights_sh,
            "flights_long_haul": flights_lh,
            "electricity_kwh": elec,
            "green_energy_pct": green,
            "cooking_gas_units": gas,
            "ac_cooling_hours_day": ac,
            "heating_hours_day": heat,
            "waste_habit": waste,
            "notes": f"Campus cohort entry #{22 + i}"
        }
        records.append(rec)

    # Write out sample_dataset_50.csv
    headers = [
        "user_name", "user_role", "month_year", "commute_mode", "commute_distance_km",
        "commute_days_per_month", "carpool_passengers", "monthly_road_trips_km",
        "flights_short_haul", "flights_long_haul", "electricity_kwh", "green_energy_pct",
        "cooking_gas_units", "ac_cooling_hours_day", "heating_hours_day", "waste_habit", "notes"
    ]
    with open(SAMPLE_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    print(f"Successfully generated {len(records)} sample dataset entries to {SAMPLE_CSV_PATH}")

    # Also pre-populate footprint_records.json and CSV with these 50 entries
    with open(RECORDS_JSON_FILE, "r", encoding="utf-8") as f:
        existing = json.load(f)

    if len(existing) < 10:
        print("Populating initial state storage with sample entries...")
        for r in records:
            val_in = validate_input_data(r)
            calc = calculate_carbon_footprint(val_in)
            save_record(val_in, calc)
        print(f"Seeded 50 initial records into footprint_records.json and CSV.")

if __name__ == "__main__":
    generate_50_dataset()
