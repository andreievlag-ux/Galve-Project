"""
Google Forms Focus Proctoring - Desktop Application Monitor Agent
------------------------------------------------------------------
Monitors OS-level process activity (Category C detection) for applications
such as Microsoft Word, Notepad, PDF Readers, ChatGPT, and unauthorized tools.

Privacy Guarantee:
- ONLY monitors running process image names and active window titles.
- NEVER reads file contents, document text, passwords, or personal data.
- Works alongside the Web Proctoring Server and Browser Extension.
"""

import time
import json
import urllib.request
import subprocess
import os
import sys

SERVER_URL = "http://localhost:8000/api/events"
STUDENT_ID = "STD-1001"
CHECK_INTERVAL_SEC = 2.0

# Standard process names mapped to event types & status
UNAUTHORIZED_PROCESSES = {
    # Microsoft Word
    "winword.exe": ("Microsoft Word Detected", "VIOLATION", "Microsoft Word (winword.exe)"),
    
    # Notepad & Text Editors
    "notepad.exe": ("Notepad / Notes Detected", "VIOLATION", "Notepad (notepad.exe)"),
    "notepad++.exe": ("Notepad++ Detected", "VIOLATION", "Notepad++ (notepad++.exe)"),
    "onenote.exe": ("OneNote Detected", "VIOLATION", "Microsoft OneNote (onenote.exe)"),
    "wordpad.exe": ("WordPad Detected", "VIOLATION", "WordPad (wordpad.exe)"),
    
    # PDF Readers & File Viewers
    "acrobrd32.exe": ("PDF Reader Detected", "VIOLATION", "Adobe Acrobat PDF Reader"),
    "acrobat.exe": ("Adobe Acrobat Pro Detected", "VIOLATION", "Adobe Acrobat PDF Reader"),
    "foxitpdfreader.exe": ("PDF Reader Detected", "VIOLATION", "Foxit PDF Reader"),
    "sumatrapdf.exe": ("SumatraPDF Reader Detected", "VIOLATION", "Sumatra PDF Viewer")
}

# Window Title Keywords to detect in browser or desktop windows
TITLE_KEYWORDS = {
    "chatgpt": ("ChatGPT Detected", "VIOLATION", "ChatGPT Browser Window"),
    "chat.openai": ("ChatGPT Detected", "VIOLATION", "ChatGPT OpenAI Window"),
    "youtube": ("YouTube Opened", "VIOLATION", "YouTube Browser Window"),
    "facebook": ("Facebook Opened", "VIOLATION", "Facebook Browser Window")
}

def get_running_windows_processes():
    """Extract running tasks and window titles on Windows using tasklist command."""
    running_apps = {}
    try:
        cmd = 'tasklist /v /fo csv'
        output = subprocess.check_output(cmd, shell=True, text=True, errors='ignore')
        lines = output.strip().split('\n')
        if len(lines) > 1:
            for line in lines[1:]:
                parts = [p.strip('"') for p in line.split('","')]
                if len(parts) >= 2:
                    image_name = parts[0].lower()
                    window_title = parts[-1] if len(parts) >= 9 else ""
                    running_apps[image_name] = window_title
    except Exception as e:
        print(f"[Agent Warning] Error scanning tasks: {e}")
    return running_apps

def post_violation_event(event_type, status, detected_item):
    """Post detected OS violation event to central proctoring server."""
    payload = {
        "student_id": STUDENT_ID,
        "event_type": event_type,
        "status": status,
        "detected_item": detected_item
    }
    try:
        req = urllib.request.Request(
            SERVER_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print(f"[ALERT SENT] -> {detected_item} | Server Response: {res_data.get('success')}")
    except Exception as e:
        print(f"[Agent Error] Could not connect to proctoring server at {SERVER_URL}: {e}")

def main():
    print("================================================================")
    print(" Google Forms Focus Proctoring - Desktop Agent (Category C)")
    print(f" Target Student ID: {STUDENT_ID}")
    print(f" Server URL: {SERVER_URL}")
    print(" Status: ACTIVE MONITORING (Press Ctrl+C to stop)")
    print("================================================================")

    last_detected_keys = set()

    while True:
        try:
            running_processes = get_running_windows_processes()
            current_detected = set()

            # 1. Process Name Check
            for proc_name, (event_type, status, label) in UNAUTHORIZED_PROCESSES.items():
                if proc_name in running_processes:
                    key = f"proc-{proc_name}"
                    current_detected.add(key)
                    if key not in last_detected_keys:
                        title_info = running_processes.get(proc_name, "")
                        full_label = f"{label} - '{title_info}'" if title_info and title_info != "N/A" else label
                        print(f"🚨 VIOLATION DETECTED: {full_label}")
                        post_violation_event(event_type, status, full_label)

            # 2. Window Title Keyword Check (ChatGPT, YouTube, etc.)
            for img, title in running_processes.items():
                if title and title != "N/A":
                    title_lower = title.lower()
                    for keyword, (event_type, status, label) in TITLE_KEYWORDS.items():
                        if keyword in title_lower:
                            key = f"title-{keyword}"
                            current_detected.add(key)
                            if key not in last_detected_keys:
                                full_label = f"{label} ({title})"
                                print(f"🚨 WINDOW TITLE VIOLATION: {full_label}")
                                post_violation_event(event_type, status, full_label)

            last_detected_keys = current_detected
            time.sleep(CHECK_INTERVAL_SEC)

        except KeyboardInterrupt:
            print("\nDesktop Agent stopped by user.")
            sys.exit(0)
        except Exception as e:
            print(f"[Agent Loop Error]: {e}")
            time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    main()
