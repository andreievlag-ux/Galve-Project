import http.server
import socketserver
import json
import urllib.parse
import os
import time
from datetime import datetime

PORT = 8000
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')

# In-memory store for sessions, events, and configuration
DEFAULT_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfD6B3xSl6aT9_sR72-R0x-SampleForm/viewform?embedded=true"

sessions = {
    "STD-1001": {
        "student_id": "STD-1001",
        "student_name": "Alex Johnson",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLScxSample_Assessment_Form/viewform?embedded=true",
        "status": "ACTIVE",  # ACTIVE, WARNING, VIOLATION
        "violations_count": 0,
        "total_unauthorized_duration_sec": 0,
        "current_unauthorized_start": None,
        "last_active": datetime.now().isoformat(),
        "current_page": "Google Form",
        "events": []
    }
}

global_config = {
    "authorized_form_url": "https://docs.google.com/forms/d/e/1FAIpQLScxSample_Assessment_Form/viewform?embedded=true",
    "allow_simulator": True,
    "warning_threshold": 3,
    "require_desktop_agent": False
}

def log_event(student_id, event_type, status, detected_item, duration_sec=0):
    if student_id not in sessions:
        sessions[student_id] = {
            "student_id": student_id,
            "student_name": f"Student {student_id}",
            "form_url": global_config["authorized_form_url"],
            "status": "ACTIVE",
            "violations_count": 0,
            "total_unauthorized_duration_sec": 0,
            "current_unauthorized_start": None,
            "last_active": datetime.now().isoformat(),
            "current_page": "Google Form",
            "events": []
        }
    
    session = sessions[student_id]
    session["last_active"] = datetime.now().isoformat()
    session["status"] = status

    if status in ["WARNING", "VIOLATION"]:
        session["violations_count"] += 1
        if not session["current_unauthorized_start"]:
            session["current_unauthorized_start"] = time.time()
    elif status == "ACTIVE" and session["current_unauthorized_start"]:
        elapsed = int(time.time() - session["current_unauthorized_start"])
        session["total_unauthorized_duration_sec"] += elapsed
        session["current_unauthorized_start"] = None

    now_str = datetime.now().strftime("%I:%M:%S %p")
    event_entry = {
        "id": f"evt-{int(time.time()*1000)}",
        "student_id": student_id,
        "timestamp": now_str,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "event_type": event_type,
        "status": status,
        "detected_item": detected_item,
        "violations_count": session["violations_count"],
        "duration_sec": duration_sec or (int(time.time() - session["current_unauthorized_start"]) if session["current_unauthorized_start"] else 0)
    }
    
    session["events"].insert(0, event_entry)
    session["current_page"] = detected_item if status != "ACTIVE" else "Google Form"
    return event_entry

# Initialize seed data
log_event("STD-1001", "Google Form active", "ACTIVE", "Google Form active")

class ProctorRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def end_headers(self):
        # Enable CORS for Chrome Extension and Desktop Agent requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/sessions":
            self.send_json_response(list(sessions.values()))
        elif parsed.path == "/api/config":
            self.send_json_response(global_config)
        elif parsed.path.startswith("/api/session/"):
            student_id = parsed.path.split("/")[-1]
            if student_id in sessions:
                self.send_json_response(sessions[student_id])
            else:
                self.send_json_response({"error": "Session not found"}, status=404)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data) if post_data else {}
        except Exception:
            data = {}

        if parsed.path == "/api/events":
            student_id = data.get("student_id", "STD-1001")
            event_type = data.get("event_type", "Unknown Event")
            status = data.get("status", "WARNING")
            detected_item = data.get("detected_item", "Unauthorized Activity")
            duration_sec = data.get("duration_sec", 0)

            event = log_event(student_id, event_type, status, detected_item, duration_sec)
            self.send_json_response({"success": True, "event": event, "session": sessions[student_id]})

        elif parsed.path == "/api/config":
            if "authorized_form_url" in data:
                global_config["authorized_form_url"] = data["authorized_form_url"]
            if "warning_threshold" in data:
                global_config["warning_threshold"] = int(data["warning_threshold"])
            self.send_json_response({"success": True, "config": global_config})

        elif parsed.path == "/api/session/reset":
            student_id = data.get("student_id")
            if student_id and student_id in sessions:
                sessions[student_id]["violations_count"] = 0
                sessions[student_id]["status"] = "ACTIVE"
                sessions[student_id]["events"] = []
                sessions[student_id]["total_unauthorized_duration_sec"] = 0
                sessions[student_id]["current_unauthorized_start"] = None
                log_event(student_id, "Google Form active", "ACTIVE", "Google Form active")
                self.send_json_response({"success": True, "session": sessions[student_id]})
            else:
                self.send_json_response({"error": "Invalid student_id"}, status=400)
        else:
            self.send_json_response({"error": "Not Found"}, status=404)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def run_server():
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with socketserver.TCPServer(("", PORT), ProctorRequestHandler) as httpd:
        print(f"==================================================")
        print(f" Google Forms Focus Proctoring Server Running!")
        print(f" Dashboard & Student Portal: http://localhost:{PORT}")
        print(f" API Endpoint: http://localhost:{PORT}/api/events")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    run_server()
