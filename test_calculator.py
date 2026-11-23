"""
Comprehensive Unit & Integration Test Suite for Campus Catalyst
Verifies:
- Computational accuracy of carbon footprint algorithms
- Defensive validation of non-conforming inputs and boundary constraints
- File persistence & auto-recovery from corrupted JSON/CSV files
- User authentication and role access
- Multi-format summary exports
- Bulk CSV parsing and row-by-row error diagnostics
"""

import unittest
import os
import json
from business_logic import (
    validate_input_data, calculate_carbon_footprint, ValidationException,
    save_record, load_all_records, query_and_filter_records,
    authenticate_user, register_user, export_summary_markdown,
    export_plain_text_audit, import_csv_dataset, initialize_storage_files,
    RECORDS_JSON_FILE, RECORDS_CSV_FILE, FootprintInput
)


class TestCarbonFootprintEngine(unittest.TestCase):

    def test_zero_emissions_lifestyle(self):
        """Walk/bike only, 100% green electricity, no AC, zero waste."""
        entry = FootprintInput(
            user_name="Green Test",
            user_role="student",
            month_year="2026-11",
            commute_distance_km=5.0,
            commute_days_per_month=20,
            commute_mode="walk_bike",
            carpool_passengers=1,
            monthly_road_trips_km=0.0,
            flights_short_haul=0,
            flights_long_haul=0,
            electricity_kwh=100.0,
            green_energy_pct=100.0, # 100% green => 0 kg electricity emissions
            cooking_gas_units=0.0,
            ac_cooling_hours_day=0.0,
            heating_hours_day=0.0,
            waste_habit="zero_waste" # -15 kg offset, floored at 0
        )
        res = calculate_carbon_footprint(entry)
        self.assertEqual(res["travel_total_kg"], 0.0)
        self.assertEqual(res["energy_total_kg"], 0.0)
        self.assertEqual(res["monthly_total_kg"], 0.0)
        self.assertEqual(res["status"], "Eco Hero")
        self.assertEqual(res["grade"], "A+")

    def test_commute_and_carpooling_logic(self):
        """Verify that carpooling divides single-passenger car emissions."""
        solo_input = FootprintInput(
            user_name="Solo", user_role="student", month_year="2026-11",
            commute_distance_km=10.0, commute_days_per_month=20, commute_mode="petrol_car",
            carpool_passengers=1, monthly_road_trips_km=0.0, flights_short_haul=0,
            flights_long_haul=0, electricity_kwh=50.0, green_energy_pct=0.0,
            cooking_gas_units=0.0, ac_cooling_hours_day=0.0, heating_hours_day=0.0,
            waste_habit="average"
        )
        solo_res = calculate_carbon_footprint(solo_input)

        carpool_input = FootprintInput(
            user_name="Carpool", user_role="student", month_year="2026-11",
            commute_distance_km=10.0, commute_days_per_month=20, commute_mode="petrol_car",
            carpool_passengers=4, monthly_road_trips_km=0.0, flights_short_haul=0,
            flights_long_haul=0, electricity_kwh=50.0, green_energy_pct=0.0,
            cooking_gas_units=0.0, ac_cooling_hours_day=0.0, heating_hours_day=0.0,
            waste_habit="average"
        )
        carpool_res = calculate_carbon_footprint(carpool_input)

        # 10 km * 20 days = 200 km. Petrol car = 0.192 kg/km -> 38.4 kg.
        # Carpool with 4 should be 38.4 / 4 = 9.6 kg.
        self.assertAlmostEqual(solo_res["travel_total_kg"], 38.4, places=1)
        self.assertAlmostEqual(carpool_res["travel_total_kg"], 9.6, places=1)

    def test_flights_and_critical_threshold(self):
        """Verify flights calculation and critical breach status trigger."""
        heavy_input = FootprintInput(
            user_name="Heavy Flyer", user_role="faculty", month_year="2026-11",
            commute_distance_km=30.0, commute_days_per_month=20, commute_mode="diesel_car",
            carpool_passengers=1, monthly_road_trips_km=100.0, flights_short_haul=2, # 300 kg
            flights_long_haul=1, # 600 kg
            electricity_kwh=300.0, green_energy_pct=0.0,
            cooking_gas_units=5.0, ac_cooling_hours_day=8.0, heating_hours_day=2.0,
            waste_habit="high_waste"
        )
        res = calculate_carbon_footprint(heavy_input)
        self.assertGreater(res["monthly_total_kg"], 450.0)
        self.assertEqual(res["status"], "Critical Breach")
        self.assertEqual(res["alert_level"], "critical")
        self.assertTrue(res["trees_needed"] > 0)


class TestDefensiveValidation(unittest.TestCase):

    def test_negative_values_rejected(self):
        bad_data = {
            "user_name": "Test User",
            "commute_distance_km": -15.0,
            "commute_days_per_month": 20,
            "commute_mode": "walk_bike",
            "electricity_kwh": 100.0
        }
        with self.assertRaises(ValidationException) as ctx:
            validate_input_data(bad_data)
        self.assertIn("commute_distance_km", ctx.exception.errors)

    def test_out_of_bound_days(self):
        bad_data = {
            "user_name": "Test User",
            "commute_distance_km": 10.0,
            "commute_days_per_month": 35, # Exceeds 31 days
            "commute_mode": "walk_bike",
            "electricity_kwh": 100.0
        }
        with self.assertRaises(ValidationException) as ctx:
            validate_input_data(bad_data)
        self.assertIn("commute_days_per_month", ctx.exception.errors)

    def test_invalid_commute_mode(self):
        bad_data = {
            "user_name": "Test User",
            "commute_distance_km": 10.0,
            "commute_days_per_month": 20,
            "commute_mode": "rocket_ship", # Not allowed
            "electricity_kwh": 100.0
        }
        with self.assertRaises(ValidationException) as ctx:
            validate_input_data(bad_data)
        self.assertIn("commute_mode", ctx.exception.errors)

    def test_non_numeric_input_handled_gracefully(self):
        bad_data = {
            "user_name": "Test User",
            "commute_distance_km": "ten kilometers", # String instead of float
            "electricity_kwh": 100.0
        }
        with self.assertRaises(ValidationException) as ctx:
            validate_input_data(bad_data)
        self.assertIn("commute_distance_km", ctx.exception.errors)


class TestFaultTolerantPersistence(unittest.TestCase):

    def test_corrupted_json_auto_repair(self):
        """Simulate a corrupted/malformed JSON file, verify initialize_storage_files repairs it safely."""
        with open(RECORDS_JSON_FILE, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON DATA CORRUPTED [")
        
        # Calling initialize_storage_files should detect JSONDecodeError and recreate clean list
        initialize_storage_files()
        records = load_all_records()
        self.assertIsInstance(records, list)

    def test_save_and_query_record(self):
        val_in = validate_input_data({
            "user_name": "Persistence Verification",
            "user_role": "student",
            "month_year": "2026-11",
            "commute_mode": "walk_bike",
            "commute_distance_km": 2.0,
            "commute_days_per_month": 15,
            "electricity_kwh": 50.0,
            "notes": "Testing record survival"
        })
        calc = calculate_carbon_footprint(val_in)
        saved = save_record(val_in, calc)
        self.assertTrue(saved["record_id"].startswith("REC-"))

        # Query back
        queried = query_and_filter_records(keyword="Persistence Verification")
        self.assertTrue(any(r["record_id"] == saved["record_id"] for r in queried))


class TestAuthentication(unittest.TestCase):

    def test_demo_login_success(self):
        user = authenticate_user("student_alex", "campus123")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "student_alex")
        self.assertEqual(user["role"], "student")

    def test_invalid_login(self):
        user = authenticate_user("student_alex", "wrong_password_XYZ")
        self.assertIsNone(user)

    def test_user_registration(self):
        import uuid
        uid = uuid.uuid4().hex[:6]
        new_username = f"test_eco_{uid}"
        registered = register_user(
            username=new_username,
            email=f"{new_username}@campus.edu",
            full_name=f"Tester Eco {uid}",
            password="securepassword123",
            role="student"
        )
        self.assertEqual(registered["username"], new_username)
        auth = authenticate_user(new_username, "securepassword123")
        self.assertIsNotNone(auth)


class TestBulkImportAndExports(unittest.TestCase):

    def test_csv_import_with_validation_logs(self):
        csv_sample = """user_name,user_role,month_year,commute_mode,commute_distance_km,commute_days_per_month,electricity_kwh
Imported Valid,student,2026-11,subway_metro,10,20,100
Imported Invalid,student,2026-11,rocket_ship,-50,99,invalid_num
"""
        result = import_csv_dataset(csv_sample)
        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["error_count"], 1)
        self.assertEqual(result["errors"][0]["user"], "Imported Invalid")

    def test_markdown_and_audit_export(self):
        md = export_summary_markdown()
        self.assertIn("Campus Catalyst - Executive Carbon Footprint Audit Report", md)
        self.assertIn("Key Performance Indicators", md)

        audit = export_plain_text_audit()
        self.assertIn("CAMPUS CATALYST CARBON FOOTPRINT SYSTEM", audit)


if __name__ == "__main__":
    unittest.main()
