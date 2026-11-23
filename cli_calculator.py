"""
Campus Catalyst - Interactive Terminal Interface (CLI)
Conforms to Core Features in Problem Brief #48:
- Menu-driven command prompt
- Defensive input validation loops
- Carbon footprint computation
- Local persistence (JSON/CSV)
- Query & search filtering
- Executive summary display & exports
"""

import os
import sys
from datetime import datetime
from business_logic import (
    initialize_storage_files, validate_input_data, calculate_carbon_footprint,
    save_record, query_and_filter_records, get_executive_summary,
    export_summary_markdown, export_plain_text_audit, import_csv_dataset,
    ValidationException, TRAVEL_EMISSION_FACTORS, WASTE_FACTORS,
    CAMPUS_AVERAGE_MONTHLY, THRESHOLD_CRITICAL
)

# ANSI terminal formatting
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[32m"
C_CYAN = "\033[36m"
C_YELLOW = "\033[33m"
C_RED = "\033[31m"
C_MAGENTA = "\033[35m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    print(f"{C_GREEN}{C_BOLD}")
    print("==========================================================================")
    print("       🌿 CAMPUS CATALYST: CARBON FOOTPRINT AWARENESS CALCULATOR          ")
    print("        Domain: Environment & Sustainability | Project #48               ")
    print("==========================================================================")
    print(f"{C_RESET}")


def prompt_defensive_float(prompt_text: str, min_val: float, max_val: float, default: float) -> float:
    while True:
        raw = input(f"{prompt_text} [{default}]: ").strip()
        if not raw:
            return default
        try:
            val = float(raw)
            if val < min_val:
                print(f"{C_RED} [!] Error: Value cannot be less than {min_val}. Try again.{C_RESET}")
                continue
            if val > max_val:
                print(f"{C_RED} [!] Error: Value cannot exceed {max_val}. Try again.{C_RESET}")
                continue
            return round(val, 2)
        except ValueError:
            print(f"{C_RED} [!] Error: Non-numeric entry detected. Please enter a valid number.{C_RESET}")


def prompt_defensive_int(prompt_text: str, min_val: int, max_val: int, default: int) -> int:
    while True:
        raw = input(f"{prompt_text} [{default}]: ").strip()
        if not raw:
            return default
        try:
            val = int(raw)
            if val < min_val:
                print(f"{C_RED} [!] Error: Value cannot be less than {min_val}. Try again.{C_RESET}")
                continue
            if val > max_val:
                print(f"{C_RED} [!] Error: Value cannot exceed {max_val}. Try again.{C_RESET}")
                continue
            return val
        except ValueError:
            print(f"{C_RED} [!] Error: Please enter a valid whole integer.{C_RESET}")


def prompt_choice(prompt_text: str, choices: list, default: str) -> str:
    print(f"\n{prompt_text}")
    for idx, c in enumerate(choices, 1):
        mark = " (default)" if c == default else ""
        print(f"  [{idx}] {c}{mark}")
    while True:
        raw = input(f"Select option [1-{len(choices)} or enter for default]: ").strip()
        if not raw:
            return default
        try:
            val = int(raw)
            if 1 <= val <= len(choices):
                return choices[val - 1]
            print(f"{C_RED} [!] Invalid choice. Enter a number between 1 and {len(choices)}.{C_RESET}")
        except ValueError:
            if raw in choices:
                return raw
            print(f"{C_RED} [!] Invalid entry. Choose from the list.{C_RESET}")


def run_new_calculation():
    print(f"\n{C_CYAN}{C_BOLD}--- Record New Carbon Footprint Assessment ---{C_RESET}")

    # User Information
    while True:
        user_name = input("Stakeholder Name / ID: ").strip()
        if user_name:
            break
        print(f"{C_RED} [!] Stakeholder name cannot be blank.{C_RESET}")

    roles = ["student", "faculty", "staff", "visitor", "auditor"]
    user_role = prompt_choice("Select Stakeholder Role:", roles, "student")
    month_year = datetime.now().strftime("%Y-%m")

    print(f"\n{C_YELLOW}>>> 1. Commute & Travel Habits{C_RESET}")
    modes = list(TRAVEL_EMISSION_FACTORS.keys())
    commute_mode = prompt_choice("Primary Commute Mode:", modes, "walk_bike")
    commute_distance_km = prompt_defensive_float("Daily round-trip commute distance (km)", 0.0, 500.0, 5.0)
    commute_days = prompt_defensive_int("Commute days per month", 0, 31, 20)
    passengers = 1
    if "car" in commute_mode:
        passengers = prompt_defensive_int("Carpooling passengers in vehicle", 1, 10, 1)

    road_trips = prompt_defensive_float("Monthly weekend / personal road trips (km)", 0.0, 5000.0, 0.0)
    flights_sh = prompt_defensive_int("Short-haul flights this month (<3 hrs)", 0, 30, 0)
    flights_lh = prompt_defensive_int("Long-haul flights this month (>3 hrs)", 0, 10, 0)

    print(f"\n{C_YELLOW}>>> 2. Campus & Living Energy Habits{C_RESET}")
    electricity_kwh = prompt_defensive_float("Monthly electricity consumption (kWh)", 0.0, 5000.0, 90.0)
    green_energy = prompt_defensive_float("Percentage of renewable / green power (%)", 0.0, 100.0, 20.0)
    cooking_gas = prompt_defensive_float("Cooking gas / LPG units consumed", 0.0, 50.0, 1.5)
    ac_hours = prompt_defensive_float("Air Conditioner (AC) usage (hours/day)", 0.0, 24.0, 2.0)
    heating_hours = prompt_defensive_float("Room Heater usage (hours/day)", 0.0, 24.0, 0.0)

    waste_habits = list(WASTE_FACTORS.keys())
    waste_habit = prompt_choice("Campus waste & recycling habit:", waste_habits, "mostly_recycle")
    notes = input("Audit Notes / Remarks (optional): ").strip()

    payload = {
        "user_name": user_name,
        "user_role": user_role,
        "month_year": month_year,
        "commute_distance_km": commute_distance_km,
        "commute_days_per_month": commute_days,
        "commute_mode": commute_mode,
        "carpool_passengers": passengers,
        "monthly_road_trips_km": road_trips,
        "flights_short_haul": flights_sh,
        "flights_long_haul": flights_lh,
        "electricity_kwh": electricity_kwh,
        "green_energy_pct": green_energy,
        "cooking_gas_units": cooking_gas,
        "ac_cooling_hours_day": ac_hours,
        "heating_hours_day": heating_hours,
        "waste_habit": waste_habit,
        "notes": notes
    }

    try:
        val_input = validate_input_data(payload)
        calc = calculate_carbon_footprint(val_input)
        record = save_record(val_input, calc)

        print(f"\n{C_GREEN}{C_BOLD}======================================================{C_RESET}")
        print(f"{C_GREEN}{C_BOLD}           ASSESSMENT SUMMARY COMPUTED                {C_RESET}")
        print(f"{C_GREEN}{C_BOLD}======================================================{C_RESET}")
        print(f" Record ID         : {record['record_id']}")
        print(f" Stakeholder       : {val_input.user_name} ({val_input.user_role.upper()})")
        print(f" Monthly Total     : {C_BOLD}{calc['monthly_total_kg']} kg CO2e{C_RESET}")
        print(f" Annualized Rate   : {calc['annual_tonnes']} Tonnes CO2e / year")
        print(f" Travel Emissions  : {calc['travel_total_kg']} kg CO2e")
        print(f" Energy Emissions  : {calc['energy_total_kg']} kg CO2e")
        print(f" Trees to Offset   : {calc['trees_needed']} mature trees")
        print(f" Ecological Status : {C_BOLD}{calc['status']} (Grade: {calc['grade']}){C_RESET}")

        if calc["alert_level"] == "critical":
            print(f"\n{C_RED}{C_BOLD} [!] THRESHOLD WARNING: CRITICAL LIMIT BREACH DETECTED!{C_RESET}")
            print(f"{C_RED} Your monthly emissions exceed the campus ceiling of {THRESHOLD_CRITICAL} kg CO2e.{C_RESET}")
        print(f"\n {C_CYAN}Recommendation:{C_RESET} {calc['advice']}")
        print(f"{C_GREEN} [✓] Record persisted to footprint_records.json and footprint_records.csv{C_RESET}")
    except ValidationException as ve:
        print(f"{C_RED} [!] Validation Error: {ve}{C_RESET}")
    except Exception as ex:
        print(f"{C_RED} [!] Unexpected error: {ex}{C_RESET}")

    input("\nPress Enter to return to main menu...")


def run_view_summary():
    summary = get_executive_summary()
    print(f"\n{C_CYAN}{C_BOLD}==========================================================================")
    print("                    EXECUTIVE SUMMARY & CAMPUS METRICS                    ")
    print(f"=========================================================================={C_RESET}")
    print(f" Total Assessed Records       : {summary['total_records']}")
    print(f" Cumulative Footprint Tracked : {summary['total_emissions_kg']:,.2f} kg CO2e")
    print(f" Average Monthly Footprint    : {summary['average_monthly_kg']:.2f} kg CO2e (Campus Target: {CAMPUS_AVERAGE_MONTHLY} kg)")
    print(f" Average Annualized Emission  : {summary['average_annual_tonnes']:.2f} Tonnes CO2e")
    print(f" Total Trees to Offset Campus : {summary['total_trees_needed']} trees")

    print(f"\n{C_YELLOW}{C_BOLD}Threshold Distribution Breakdown:{C_RESET}")
    for st, count in summary["status_counts"].items():
        bar = "█" * min(30, count * 2)
        print(f"  {st:<22}: {count:>3} records | {bar}")

    print(f"\n{C_YELLOW}{C_BOLD}Monthly Historical Trends:{C_RESET}")
    print(f"  {'Month':<10} {'Avg Total (kg)':<16} {'Avg Travel (kg)':<16} {'Avg Energy (kg)':<16} {'Entries'}")
    print("  " + "-" * 66)
    for t in summary["monthly_trends"]:
        print(f"  {t['month']:<10} {t['avg_monthly_kg']:<16.1f} {t['avg_travel_kg']:<16.1f} {t['avg_energy_kg']:<16.1f} {t['entries_count']}")

    input("\nPress Enter to return to main menu...")


def run_query_records():
    print(f"\n{C_CYAN}{C_BOLD}--- Query & Search Local Records ---{C_RESET}")
    kw = input("Enter search keyword (name, notes, ID, or leave blank): ").strip()
    status_filter = input("Filter by status (Eco Hero, Critical Breach, or leave blank): ").strip()
    sort_choice = input("Sort by [1=Newest, 2=Highest Emissions, 3=Lowest Emissions]: ").strip()

    sort_map = {"1": "newest", "2": "highest_emissions", "3": "lowest_emissions"}
    sort_by = sort_map.get(sort_choice, "newest")

    results = query_and_filter_records(keyword=kw or None, status=status_filter or None, sort_by=sort_by)

    print(f"\nFound {len(results)} matching records:")
    print("-" * 78)
    print(f"{'ID':<12} {'NAME':<18} {'ROLE':<8} {'MONTH':<8} {'TOTAL (kg)':<12} {'GRADE':<6} {'STATUS'}")
    print("-" * 78)

    for r in results[:20]:
        inp = r.get("input", {})
        calc = r.get("calculation", {})
        print(
            f"{r.get('record_id', ''):<12} "
            f"{inp.get('user_name', '')[:16]:<18} "
            f"{inp.get('user_role', '')[:8]:<8} "
            f"{inp.get('month_year', ''):<8} "
            f"{str(calc.get('monthly_total_kg', 0)):<12} "
            f"{calc.get('grade', '-'):<6} "
            f"{calc.get('status', '-')}"
        )

    if len(results) > 20:
        print(f"  ... and {len(results) - 20} more records.")

    input("\nPress Enter to return to main menu...")


def run_export_menu():
    print(f"\n{C_CYAN}{C_BOLD}--- Multi-Format Summary Exporters ---{C_RESET}")
    print("  [1] Generate Structured Markdown Audit Report (.md)")
    print("  [2] Generate Plain-Text System Audit Log (.txt)")
    print("  [3] Verify Local CSV Persistence File (.csv)")
    choice = input("Select format [1-3]: ").strip()

    if choice == "1":
        content = export_summary_markdown()
        out_file = os.path.join(os.getcwd(), "campus_carbon_report.md")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"{C_GREEN} [✓] Markdown audit report exported to {out_file}{C_RESET}")
    elif choice == "2":
        content = export_plain_text_audit()
        out_file = os.path.join(os.getcwd(), "campus_carbon_audit.txt")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"{C_GREEN} [✓] Plain-text audit log exported to {out_file}{C_RESET}")
    elif choice == "3":
        csv_file = os.path.join(os.getcwd(), "data", "footprint_records.csv")
        if os.path.exists(csv_file):
            size = os.path.getsize(csv_file)
            print(f"{C_GREEN} [✓] CSV file verified at {csv_file} ({size} bytes).{C_RESET}")
        else:
            print(f"{C_RED} [!] CSV file not yet created.{C_RESET}")

    input("\nPress Enter to return to main menu...")


def run_bulk_import_menu():
    print(f"\n{C_CYAN}{C_BOLD}--- Bulk Dataset CSV Ingestion ---{C_RESET}")
    sample_path = os.path.join(os.getcwd(), "data", "sample_dataset_50.csv")
    csv_file = input(f"Enter path to CSV file [Default: {sample_path}]: ").strip()
    if not csv_file:
        csv_file = sample_path

    if not os.path.exists(csv_file):
        print(f"{C_RED} [!] File not found: {csv_file}{C_RESET}")
        input("Press Enter to return...")
        return

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            content = f.read()
        res = import_csv_dataset(content)
        print(f"\n{C_GREEN} [✓] Bulk ingestion complete!{C_RESET}")
        print(f"  Valid records saved  : {res['success_count']}")
        print(f"  Invalid rows rejected: {res['error_count']}")
        if res["errors"]:
            print(f"\n{C_YELLOW}Validation Error Log:{C_RESET}")
            for err in res["errors"][:5]:
                print(f"  Row {err['row']} ({err['user']}): {err['error']}")
    except Exception as e:
        print(f"{C_RED} [!] Import failed: {e}{C_RESET}")

    input("\nPress Enter to return to main menu...")


def main():
    initialize_storage_files()
    while True:
        clear_screen()
        print_banner()
        print(" [1] ➕ Record New Carbon Footprint Assessment")
        print(" [2] 📊 View Executive Summary & Campus Metrics")
        print(" [3] 🔍 Query & Search Local Assessment Records")
        print(" [4] 📥 Ingest Bulk CSV Dataset with Validation Logs")
        print(" [5] 📤 Export Summary Reports (Markdown, TXT, CSV)")
        print(" [6] 🌐 Launch Web Server (Website & Login Page)")
        print(" [7] ❌ Exit Application")
        print("--------------------------------------------------------------------------")
        choice = input("Select an option [1-7]: ").strip()

        if choice == "1":
            run_new_calculation()
        elif choice == "2":
            run_view_summary()
        elif choice == "3":
            run_query_records()
        elif choice == "4":
            run_bulk_import_menu()
        elif choice == "5":
            run_export_menu()
        elif choice == "6":
            print(f"\n{C_GREEN}Starting web application server on http://localhost:8080...{C_RESET}")
            from app import run_server
            run_server(8080)
        elif choice == "7":
            print("\nExiting Campus Catalyst. Keep your footprint low!\n")
            sys.exit(0)
        else:
            print(f"{C_RED}Invalid option selected. Try again.{C_RESET}")


if __name__ == "__main__":
    main()
