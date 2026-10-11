# FormSentry Guard - Google Forms Assessment Focus Proctoring System

**FormSentry Guard** is a multi-layered proctoring system engineered specifically to enforce student focus on an authorized Google Form during an assessment or activity.

---

## 🎯 Key Capabilities & Detection Layers

The system accurately detects and logs unauthorized activities across three distinct monitoring environments:

| Required Activity | Category A: Webpage Layer | Category B: Browser Extension Layer | Category C: OS Desktop Agent |
| :--- | :--- | :--- | :--- |
| **1. Leaving Google Form** | 🟢 Page Visibility API & `window.blur` | 🟢 `chrome.tabs.onActivated` | 🟢 Active Window Title Tracking |
| **2. Opening Another Webpage** | 🟡 Detects Focus Loss | 🟢 `chrome.webNavigation` & Domain Tracking | 🟢 Browser Window Titles |
| **3. Using ChatGPT** | 🟡 Detects Focus Loss | 🟢 URL matching (`chatgpt.com`, `chat.openai.com`) | 🟢 Window Title Matching |
| **4. Opening Microsoft Word** | 🔴 Sandboxed (Not possible) | 🔴 Sandboxed (Not possible) | 🟢 Process Scanner (`winword.exe`) |
| **5. Opening Notes / Notepad** | 🔴 Sandboxed (Not possible) | 🔴 Sandboxed (Not possible) | 🟢 Process Scanner (`notepad.exe`, `onenote.exe`) |
| **6. Opening PDF / Files** | 🔴 Sandboxed (Not possible) | 🟡 Browser PDF tabs | 🟢 Process Scanner (`AcroRd32.exe`, `Foxit`, viewers) |

---

## ⚠️ Warning System Specification

Whenever an unauthorized activity is detected, an overlay notification modal appears:

```text
=========================================================
                      WARNING #2
        Unauthorized activity detected:
        ChatGPT was opened.

        Please return to the authorized Google Form.
=========================================================
Metadata Included:
- Violation Type: ChatGPT Opened (chatgpt.com)
- Date & Time: 2026-10-08 10:05:21 AM
- Violations Count: #2
- Required Action: "Return to Google Form"
```

---

## 📊 Administrator Dashboard

The Admin Dashboard provides real-time oversight:
- **Active Candidates & Status Badges**:
  - 🟢 **ACTIVE** – User is on the authorized Google Form
  - 🟡 **WARNING** – Possible unauthorized activity / tab focus loss detected
  - 🔴 **VIOLATION** – Unauthorized webpage or desktop application detected
- **Real-Time Violation Stream**:
  - Timestamps, Student ID, Event Type, Detected App/Page, Violation #, Unauthorized Duration.
- **Log Search & Filtering**: Filter by status (ACTIVE, WARNING, VIOLATION) or search candidate ID.
- **CSV Data Export**: One-click export of exam logs for institution record-keeping.

---

## 🛡️ Privacy & Security Boundaries

FormSentry Guard strictly adheres to student privacy standard policies:
- ❌ **Does NOT** read personal files or hard drive contents.
- ❌ **Does NOT** read document text inside Microsoft Word, Notes, or PDFs.
- ❌ **Does NOT** record passwords, keystrokes, or private chat messages.
- ❌ **Does NOT** perform hidden background monitoring without user knowledge.
- 🟢 **Only** monitors process image names and window focus/URLs needed for assessment integrity.

---

## 🚀 Quickstart & Setup Guide

### 1. Launch Central Server & Web App
```powershell
python server.py
```
Open **`http://localhost:8000`** in Google Chrome or any modern browser.

### 2. (Optional) Run OS Desktop Agent (Category C Monitoring)
To detect Microsoft Word (`winword.exe`), Notepad (`notepad.exe`), or PDF Readers (`AcroRd32.exe`):
```powershell
python desktop_agent.py
```

### 3. (Optional) Load Chrome Extension (Category B Monitoring)
1. Open Chrome and navigate to `chrome://extensions`.
2. Enable **Developer mode** (top right toggle).
3. Click **Load unpacked** and select the `extension/` directory inside this workspace.

---

## 📁 Repository Structure

```text
├── server.py             # Python HTTP & REST API Proctor Server
├── desktop_agent.py      # Category C Windows Desktop Process Scanner
├── extension/            # Category B Chrome Manifest V3 Extension
│   ├── manifest.json
│   ├── background.js
│   └── content.js
├── public/               # Web App Frontend
│   ├── index.html        # Main Proctor Portal & Admin Dashboard UI
│   ├── style.css         # Modern Dark Glassmorphism CSS Design
│   └── app.js            # Client-side Visibility API & WS Sync Logic
└── README.md             # System Documentation
```
