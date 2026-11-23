"""
Campus Catalyst - Web Server & REST API
Built using Python 3.10+ Standard Library ThreadingHTTPServer.
Provides static file serving and JSON API for the Carbon Footprint Awareness Web Application.
"""

import os
import sys
import json
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

from business_logic import (
    initialize_storage_files, validate_input_data, calculate_carbon_footprint,
    save_record, query_and_filter_records, delete_record_by_id,
    get_executive_summary, import_csv_dataset, export_summary_markdown,
    export_plain_text_audit, authenticate_user, register_user,
    ValidationException, RECORDS_CSV_FILE, DATA_DIR, BASE_DIR
)

STATIC_DIR = os.path.join(BASE_DIR, "static")
SAMPLE_CSV_PATH = os.path.join(DATA_DIR, "sample_dataset_50.csv")

# Active in-memory session tokens (token -> user dict)
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}


class CampusCatalystHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Keep terminal output clean
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: int = 400, errors: Any = None):
        payload = {"success": False, "error": message}
        if errors:
            payload["details"] = errors
        self.send_json(payload, status=status)

    def send_file_download(self, content: bytes, filename: str, content_type: str = "text/plain"):
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise ValidationException("Malformed JSON request body.")

    def read_text_body(self) -> str:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return ""
        return self.rfile.read(content_length).decode("utf-8", errors="replace")

    # ==========================
    # GET Handlers
    # ==========================
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API: Records Query & Search
        if path == "/api/records":
            kw = query.get("keyword", [None])[0]
            cat = query.get("category", [None])[0]
            st = query.get("status", [None])[0]
            role = query.get("role", [None])[0]
            sort_by = query.get("sort_by", ["newest"])[0]

            records = query_and_filter_records(keyword=kw, category=cat, status=st, role=role, sort_by=sort_by)
            self.send_json({"success": True, "count": len(records), "records": records})
            return

        # 2. API: Executive Summary & Analytics
        if path == "/api/summary":
            summary = get_executive_summary()
            self.send_json({"success": True, "summary": summary})
            return

        # 3. API: Multi-Format Summary Exporters
        if path == "/api/export":
            fmt = query.get("format", ["markdown"])[0].lower()
            if fmt == "markdown" or fmt == "md":
                content = export_summary_markdown().encode("utf-8")
                self.send_file_download(content, "campus_carbon_summary.md", "text/markdown")
                return
            elif fmt == "audit" or fmt == "txt":
                content = export_plain_text_audit().encode("utf-8")
                self.send_file_download(content, "carbon_audit_log.txt", "text/plain")
                return
            elif fmt == "csv":
                if os.path.exists(RECORDS_CSV_FILE):
                    with open(RECORDS_CSV_FILE, "rb") as f:
                        content = f.read()
                else:
                    content = b"record_id,created_at,user_name,status\n"
                self.send_file_download(content, "campus_footprint_records.csv", "text/csv")
                return
            else:
                self.send_error_json("Invalid export format. Choose markdown, audit, or csv.", 400)
                return

        # 4. API: Sample 50-Record Dataset Download
        if path == "/api/sample-csv":
            if os.path.exists(SAMPLE_CSV_PATH):
                with open(SAMPLE_CSV_PATH, "rb") as f:
                    content = f.read()
                self.send_file_download(content, "sample_dataset_50.csv", "text/csv")
            else:
                self.send_error_json("Sample dataset not found.", 404)
            return

        # 5. Static Files Serving
        self.serve_static(path)

    # ==========================
    # POST Handlers
    # ==========================
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. API: User Authentication (Login)
        if path == "/api/auth/login":
            try:
                body = self.read_json_body()
                username = body.get("username", "")
                password = body.get("password", "")
                user = authenticate_user(username, password)
                if not user:
                    self.send_error_json("Invalid username/email or password.", 401)
                    return
                # Create session token
                import uuid
                token = "sess_" + uuid.uuid4().hex
                ACTIVE_SESSIONS[token] = user
                self.send_json({"success": True, "token": token, "user": user})
            except Exception as e:
                self.send_error_json(str(e), 500)
            return

        # 2. API: User Registration
        if path == "/api/auth/register":
            try:
                body = self.read_json_body()
                user = register_user(
                    username=body.get("username", ""),
                    email=body.get("email", ""),
                    full_name=body.get("full_name", ""),
                    password=body.get("password", ""),
                    role=body.get("role", "student")
                )
                import uuid
                token = "sess_" + uuid.uuid4().hex
                ACTIVE_SESSIONS[token] = user
                self.send_json({"success": True, "token": token, "user": user})
            except ValidationException as ve:
                self.send_error_json(str(ve), 400, ve.errors)
            except Exception as e:
                self.send_error_json(str(e), 500)
            return

        # 3. API: Live Real-time Footprint Calculation Preview
        if path == "/api/calculate":
            try:
                body = self.read_json_body()
                validated_input = validate_input_data(body)
                calc_result = calculate_carbon_footprint(validated_input)
                self.send_json({"success": True, "calculation": calc_result})
            except ValidationException as ve:
                self.send_error_json(str(ve), 422, ve.errors)
            except Exception as e:
                self.send_error_json(f"Calculation error: {str(e)}", 500)
            return

        # 4. API: Save New Footprint Record
        if path == "/api/records":
            try:
                body = self.read_json_body()
                validated_input = validate_input_data(body)
                calc_result = calculate_carbon_footprint(validated_input)
                saved_record = save_record(validated_input, calc_result)
                self.send_json({
                    "success": True,
                    "message": "Record successfully calculated and persisted to local JSON/CSV.",
                    "record": saved_record
                }, status=201)
            except ValidationException as ve:
                self.send_error_json(str(ve), 422, ve.errors)
            except Exception as e:
                self.send_error_json(f"Persistence error: {str(e)}", 500)
            return

        # 5. API: Bulk Dataset Import
        if path == "/api/import":
            try:
                content_type = self.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    body = self.read_json_body()
                    csv_text = body.get("csv_data", "")
                else:
                    csv_text = self.read_text_body()

                if not csv_text.strip():
                    self.send_error_json("No CSV content provided for import.", 400)
                    return

                res = import_csv_dataset(csv_text)
                self.send_json({
                    "success": True,
                    "message": f"Dataset processed: {res['success_count']} saved, {res['error_count']} rejected.",
                    "result": res
                })
            except Exception as e:
                self.send_error_json(f"Bulk import failed: {str(e)}", 500)
            return

        self.send_error_json("Endpoint not found", 404)

    # ==========================
    # DELETE Handlers
    # ==========================
    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/records/"):
            record_id = path.split("/api/records/")[-1].strip()
            if not record_id:
                self.send_error_json("Missing record ID", 400)
                return
            success = delete_record_by_id(record_id)
            if success:
                self.send_json({"success": True, "message": f"Record {record_id} successfully deleted."})
            else:
                self.send_error_json(f"Record {record_id} not found.", 404)
            return

        self.send_error_json("Endpoint not found", 404)

    # ==========================
    # Static Files Serving
    # ==========================
    def serve_static(self, path: str):
        if path in ["/", "/index.html", "/dashboard", "/calculator"]:
            file_path = os.path.join(STATIC_DIR, "index.html")
        elif path in ["/login", "/login.html"]:
            file_path = os.path.join(STATIC_DIR, "login.html")
        else:
            rel_path = path.lstrip("/")
            file_path = os.path.join(STATIC_DIR, rel_path)

        # Normalize and guard against directory traversal
        file_path = os.path.abspath(file_path)
        if not file_path.startswith(STATIC_DIR):
            self.send_error_json("Access denied", 403)
            return

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            # Fallback to index.html for SPA routes
            file_path = os.path.join(STATIC_DIR, "index.html")

        # Determine MIME type
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".csv": "text/csv; charset=utf-8"
        }
        content_type = mime_types.get(ext, "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error_json(f"Error reading file: {str(e)}", 500)


def run_server(port: int = 8080):
    initialize_storage_files()
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, CampusCatalystHandler)
    print(f"==================================================")
    print(f"🌿 Campus Catalyst Web Application Server")
    print(f"🚀 Running at: http://localhost:{port}")
    print(f"🔐 Login Page: http://localhost:{port}/#login")
    print(f"📊 Dashboard:  http://localhost:{port}/#dashboard")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully.")
        httpd.server_close()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
