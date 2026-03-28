# RenalWatch — System Architecture & Build Guide

> **What it is:** An outpatient CKD monitoring system that tracks BP from a wearable device, monitors for anomalies, sends patient reminders, runs a WhatsApp symptom check-in chatbot, and relays trend data to the doctor in an explainable way.
>
> **What it is NOT:** A diagnostic tool. RenalWatch monitors and alerts — it does not diagnose.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Tech Stack](#2-tech-stack)
3. [Folder Structure](#3-folder-structure)
4. [Database Models](#4-database-models)
5. [API Routes](#5-api-routes)
6. [Services](#6-services)
7. [ML Engine](#7-ml-engine)
8. [Workers](#8-workers)
9. [Integrations](#9-integrations)
10. [Docker Setup](#10-docker-setup)
11. [Environment Variables](#11-environment-variables)
12. [Build Order](#12-build-order)
13. [Dashboard Contract](#13-dashboard-contract)
14. [WhatsApp Chatbot Flow](#14-whatsapp-chatbot-flow)

---

## 1. System Overview

```
[ZFit Smartwatch]
      |
      | (Bluetooth sync to phone)
      |
[ZFit App on Android Phone]
      |
      | (ADB polling via USB — fitPro.db)
      |
[ADB Worker] ──────────────────────────────────────────────────────────┐
      |                                                                 |
      ↓                                                                 |
[FastAPI Backend]                                                       |
      |                                                                 |
      ├─── /readings    ← Ingest + store BP readings                    |
      ├─── /patients    ← Patient CRUD                                  |
      ├─── /alerts      ← Alert history                                 |
      ├─── /chatbot     ← WhatsApp webhook handler                     |
      └─── /dashboard   ← Doctor trend data + explainability           |
      |                                                                 |
      ↓                                                                 |
[ML Engine]                                                             |
      ├─── features.py  → Rolling mean, delta, std (time-series feats) |
      ├─── anomaly.py   → Isolation Forest inference                   |
      ├─── rules.py     → Fuzzy Logic severity classification          |
      └─── explain.py   → Human-readable explanation strings           |
      |                                                                 |
      ↓                                                                 |
[PostgreSQL Database]                                                   |
      ├─── patients                                                     |
      ├─── bp_readings                                                  |
      ├─── alerts                                                       |
      ├─── symptom_logs                                                 |
      └─── reminders                                                    |
      |                                                                 |
      ↓                                                                 |
[Notification Service]                                                  |
      ├─── Africa's Talking → SMS to patient/doctor                    |
      └─── SMTP (Gmail)    → Email alerts                              |
                                                                        |
[Scheduler Worker] ─────────────────────────────────────────────────────┘
      └─── Periodic medication/check-in reminders via SMS
```

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Containerization | Docker + Docker Compose |
| ML — anomaly detection | scikit-learn (Isolation Forest) |
| ML — severity classification | scikit-fuzzy (fuzzy logic, rule-based) |
| Data processing | pandas, numpy |
| SMS/alerts | Africa's Talking |
| Email | smtplib (Gmail SMTP) |
| WhatsApp chatbot | Africa's Talking WhatsApp API |
| Model persistence | joblib |
| Watch data source | ADB → SQLite (fitPro.db) |

---

## 3. Folder Structure

```
RenalWatch/
├── app/
│   ├── main.py                        # FastAPI app entry point
│   │
│   ├── core/
│   │   └── config.py                  # Env vars via pydantic-settings
│   │
│   ├── db/
│   │   ├── base.py                    # SQLAlchemy DeclarativeBase
│   │   └── session.py                 # Async DB session + dependency
│   │
│   ├── models/                        # SQLAlchemy ORM models (tables)
│   │   ├── patient.py
│   │   ├── bp_reading.py
│   │   ├── alert.py
│   │   ├── symptom_log.py
│   │   └── reminder.py
│   │
│   ├── schemas/                       # Pydantic request/response schemas
│   │   ├── patient.py
│   │   ├── bp_reading.py
│   │   └── symptom_log.py
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── patients.py            # CRUD for patients
│   │       ├── readings.py            # Ingest + retrieve BP readings
│   │       ├── alerts.py              # Alert history
│   │       ├── chatbot.py             # WhatsApp webhook
│   │       └── dashboard.py          # Doctor dashboard data
│   │
│   ├── services/
│   │   ├── alert_service.py           # Decide when/what to alert
│   │   ├── notification_service.py    # Fire SMS + Email
│   │   └── chatbot_service.py         # Stateful chatbot logic
│   │
│   ├── ml/
│   │   ├── features.py                # Time-series feature engineering
│   │   ├── anomaly.py                 # Isolation Forest inference
│   │   ├── rules.py                   # Fuzzy logic rules
│   │   └── explain.py                 # Explainability strings
│   │
│   └── integrations/
│       ├── africas_talking.py         # AT SDK wrapper
│       ├── email.py                   # SMTP wrapper
│       └── zfit_adb.py                # ADB pull + DB query
│
├── workers/
│   ├── adb_worker.py                  # Polls fitPro.db every 30s
│   └── scheduler.py                  # Fires periodic reminders
│
├── ml/
│   └── training/
│       └── train_isolation_forest.py  # One-time training script
│
├── alembic/
│   ├── versions/                      # Auto-generated migration files
│   └── env.py                         # Alembic config (edit this)
│
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── .env
└── requirements.txt
```

---

## 4. Database Models

### `patients`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | Auto |
| name | String | Full name |
| phone | String | E.164 format e.g. +2547XXXXXXXX |
| email | String | Optional |
| age | Integer | |
| ckd_stage | Integer | 1–5 |
| created_at | DateTime | Auto |

### `bp_readings`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| patient_id | FK → patients | |
| systolic | Float | mmHg |
| diastolic | Float | mmHg |
| timestamp | DateTime | When reading was taken on watch |
| source | String | "wearable" or "manual" |
| anomaly_score | Float | From Isolation Forest |
| is_anomaly | Integer | 0 or 1 |
| fuzzy_severity | String | "normal", "elevated", "stage1", "stage2", "crisis" |
| explanation | String | Human-readable reason string |

### `alerts`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| patient_id | FK → patients | |
| alert_type | String | "spike", "stage2", "crisis", "missed_reading" |
| message | String | Alert body text |
| severity | String | "low", "medium", "high", "critical" |
| sent_via | String | "sms", "email", "both" |
| triggered_at | DateTime | |
| explanation | String | XAI audit trail (required) |

### `symptom_logs`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| patient_id | FK → patients | |
| fatigue | Integer | 1–10 scale |
| pain_level | Integer | 1–10 scale |
| swelling | Integer | 1–10 scale |
| nausea | Integer | 1–10 scale |
| notes | String | Free text |
| chat_step | String | Chatbot state ("start", "fatigue", "pain", "done") |
| logged_at | DateTime | |

### `reminders`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| patient_id | FK → patients | |
| reminder_type | String | "medication", "bp_check", "appointment" |
| message | String | |
| scheduled_at | DateTime | When to fire |
| sent | Integer | 0 or 1 |

---

## 5. API Routes

### Patients — `/patients`
| Method | Path | Description |
|---|---|---|
| POST | `/patients/` | Register new patient |
| GET | `/patients/` | List all patients |
| GET | `/patients/{id}` | Get one patient |
| PUT | `/patients/{id}` | Update patient info |

### BP Readings — `/readings`
| Method | Path | Description |
|---|---|---|
| POST | `/readings/` | Ingest a new BP reading (called by adb_worker) |
| GET | `/readings/{patient_id}` | Get reading history for a patient |
| GET | `/readings/{patient_id}/latest` | Get most recent reading |

### Alerts — `/alerts`
| Method | Path | Description |
|---|---|---|
| GET | `/alerts/{patient_id}` | Get alert history for a patient |

### Dashboard — `/dashboard`
| Method | Path | Description |
|---|---|---|
| GET | `/dashboard/{patient_id}` | Full trend + anomaly + explanation data for doctor |

### Chatbot — `/chatbot`
| Method | Path | Description |
|---|---|---|
| POST | `/chatbot/webhook` | Africa's Talking WhatsApp webhook receiver |

---

## 6. Services

### `alert_service.py`
**Responsibility:** Given a new BP reading with its ML outputs, decide whether to fire an alert and what kind.

Logic:
```
if is_anomaly == 1 AND fuzzy_severity in ["stage2", "crisis"]:
    → fire alert (type = "spike")
if fuzzy_severity == "crisis" regardless of anomaly:
    → fire alert (type = "crisis")
```

Saves alert to DB with explanation string. Calls notification_service.

### `notification_service.py`
**Responsibility:** Send the actual SMS and/or email.

- Uses `integrations/africas_talking.py` for SMS
- Uses `integrations/email.py` for email
- Sends to both patient and doctor on critical alerts
- Logs `sent_via` back to the alert record

### `chatbot_service.py`
**Responsibility:** Handle incoming WhatsApp messages step by step.

Stateful conversation stored in `symptom_logs.chat_step`.

Flow:
```
step 1 → "How are you feeling today? (1-10)"    → saves fatigue
step 2 → "Any pain? Rate 1-10"                  → saves pain_level
step 3 → "Any swelling in legs/ankles? (1-10)"  → saves swelling
step 4 → "Feeling nauseous? (1-10)"             → saves nausea
step 5 → "Anything else to tell your doctor?"   → saves notes
done   → "Thank you. Your doctor has been notified."
```

Relays completed log to alert_service for doctor notification.

---

## 7. ML Engine

### `features.py`
**Critical:** Isolation Forest needs time-series features, not just raw BP values.

Features to compute from recent readings:
```python
features = {
    "systolic":        current systolic,
    "diastolic":       current diastolic,
    "rolling_mean_5":  mean of last 5 systolic readings,
    "rolling_std_5":   std of last 5 systolic readings,
    "delta_1":         difference from previous reading,
    "delta_3":         difference from reading 3 ago,
    "time_gap_hrs":    hours since last reading
}
```

### `anomaly.py`
Loads trained Isolation Forest model and runs inference.

```python
model = joblib.load("ml/models/isolation_forest.pkl")
score = model.decision_function([features])   # negative = more anomalous
prediction = model.predict([features])        # -1 = anomaly, 1 = normal
```

### `rules.py`
Fuzzy logic — rule-based, NO training needed. Uses AHA/ACC BP guidelines.

Membership functions:
```
Normal:   systolic < 120,  diastolic < 80
Elevated: systolic 120-129
Stage 1:  systolic 130-139, diastolic 80-89
Stage 2:  systolic ≥ 140,  diastolic ≥ 90
Crisis:   systolic > 180,  diastolic > 120
```

Output: severity label + degree of membership (e.g. "70% Stage 1, 30% Elevated")

### `explain.py`
Converts ML outputs into human-readable strings for the doctor dashboard.

```python
def explain(reading, score, severity):
    reasons = []
    if reading.is_anomaly:
        reasons.append(f"Sudden BP spike detected (anomaly score: {score:.2f})")
    if reading.delta_1 > 20:
        reasons.append(f"BP rose {reading.delta_1:.0f} mmHg from previous reading")
    reasons.append(f"Classified as {severity} by fuzzy logic rules")
    return "; ".join(reasons)
```

---

## 8. Workers

### `adb_worker.py`
Runs as a separate Docker container. Polls every 30 seconds.

```
1. adb pull /sdcard/Android/data/com.legend.simsonlab.app.android/db/fitPro ./fitPro.db
2. Read latest row from MEASURE_BLOOD_MODEL
3. If new reading (different _id from last seen):
   a. POST to /readings/ endpoint with systolic, diastolic, timestamp
   b. Update last_seen_id
4. Sleep 30 seconds
5. Repeat
```

Column mapping from fitPro.db:
```
MEASURE_BLOOD_MODEL columns: _id, DEVID, DATE, systolic(col4), diastolic(col5)
DATE is Unix timestamp in milliseconds → divide by 1000 for Python datetime
```

### `scheduler.py`
Fires periodic reminders for medication and BP check-ins.

```
Every morning 8am  → "Time to take your medication, [name]"
Every evening 6pm  → "Please take your BP reading for today"
Weekly             → "Your doctor check-in is due. Open the app to log symptoms."
```

Uses `asyncio` sleep loop — no Redis/Celery needed for MVP.

---

## 9. Integrations

### `integrations/africas_talking.py`
```python
import africastalking

africastalking.initialize(username=settings.AT_USERNAME, api_key=settings.AT_API_KEY)
sms = africastalking.SMS

def send_sms(phone: str, message: str):
    return sms.send(message, [phone])
```

### `integrations/email.py`
```python
import smtplib
from email.mime.text import MIMEText

def send_email(to: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_EMAIL
    msg["To"] = to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.send_message(msg)
```

### `integrations/zfit_adb.py`
```python
import subprocess, sqlite3

REMOTE_PATH = "/sdcard/Android/data/com.legend.simsonlab.app.android/db/fitPro"
LOCAL_PATH  = "./fitPro.db"

def pull_db():
    subprocess.run(["adb", "pull", REMOTE_PATH, LOCAL_PATH], capture_output=True)

def get_latest_bp():
    conn = sqlite3.connect(LOCAL_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT _id, DATE, col4, col5 FROM MEASURE_BLOOD_MODEL ORDER BY _id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row  # (_id, timestamp_ms, systolic, diastolic)
```

---

## 10. Docker Setup

### `docker-compose.yml`
```yaml
version: "3.9"

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: renal
      POSTGRES_PASSWORD: renal123
      POSTGRES_DB: renalwatch
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  worker:
    build: .
    command: python workers/adb_worker.py
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db

volumes:
  pg_data:
```

### `Dockerfile`
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Startup Commands
```bash
# First time setup
docker-compose up --build

# Run migrations (in a new terminal)
docker-compose exec api alembic revision --autogenerate -m "initial tables"
docker-compose exec api alembic upgrade head

# View API docs
# Open http://localhost:8000/docs
```

---

## 11. Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://renal:renal123@db:5432/renalwatch
AT_API_KEY=your_africas_talking_live_api_key
AT_USERNAME=your_africas_talking_username
SMTP_EMAIL=your@gmail.com
SMTP_PASSWORD=your_gmail_app_password
DOCTOR_PHONE=+2547XXXXXXXX
DOCTOR_EMAIL=doctor@hospital.com
```

**Note on Gmail App Password:** Go to Google Account → Security → 2-Step Verification → App Passwords → Generate one for "Mail".

**Note on Africa's Talking:** Use `sandbox` as username and sandbox API key for testing. Switch to live credentials + top up M-Pesa for real SMS.

---

## 12. Build Order

Build in this exact order — each step depends on the previous.

```
Step 1: DB Models + Alembic migration
        → patients, bp_readings, alerts, symptom_logs, reminders

Step 2: FastAPI app skeleton + /patients CRUD
        → Confirm DB connection works

Step 3: /readings route
        → POST a reading manually and confirm it stores

Step 4: Rule-based alerts (NO ML yet)
        → if systolic > 180: fire alert
        → Confirm SMS lands on phone via Africa's Talking

Step 5: ADB worker
        → Confirm real watch data flows into /readings automatically

Step 6: Notification service
        → SMS + Email working end to end

Step 7: Scheduler worker
        → Medication reminders firing on schedule

Step 8: WhatsApp chatbot
        → Full symptom check-in flow working

Step 9: ML — train Isolation Forest (needs data from steps above)
        → Fuzzy logic rules
        → Explainability strings

Step 10: /dashboard route
         → Full doctor view with trend, anomalies, explanations
```

---

## 13. Dashboard Contract

The `/dashboard/{patient_id}` endpoint must return exactly this shape:

```json
{
  "patient_id": 1,
  "patient_name": "John Doe",
  "ckd_stage": 3,
  "trend": [
    { "timestamp": "2025-03-28T08:00:00", "systolic": 138, "diastolic": 88 },
    { "timestamp": "2025-03-28T09:00:00", "systolic": 142, "diastolic": 91 }
  ],
  "moving_avg": [
    { "timestamp": "2025-03-28T08:00:00", "systolic_avg": 139 }
  ],
  "anomalies": [
    { "timestamp": "2025-03-28T09:00:00", "systolic": 195, "score": -0.23 }
  ],
  "risk_level": "HIGH",
  "explanation": [
    "BP rising trend over the last 72 hours",
    "Sudden spike detected — 53 mmHg rise from previous reading",
    "Classified as Stage 2 Hypertension by fuzzy logic rules",
    "Patient reported fatigue level 8/10 in last check-in"
  ]
}
```

The `explanation` array is mandatory — it is the explainability requirement.

---

## 14. WhatsApp Chatbot Flow

Africa's Talking sends a POST to `/chatbot/webhook` every time the patient replies.

```
Doctor/system sends: "Hi [name], time for your weekly check-in. How are you feeling? Rate your energy 1-10."

Patient replies: "6"
  → save fatigue=6, advance step to "pain"
  → reply: "Thanks. Any pain today? Rate 1-10."

Patient replies: "4"
  → save pain_level=4, advance step to "swelling"
  → reply: "Any swelling in your legs or ankles? Rate 1-10."

Patient replies: "2"
  → save swelling=2, advance step to "nausea"
  → reply: "Feeling nauseous at all? Rate 1-10."

Patient replies: "1"
  → save nausea=1, advance step to "notes"
  → reply: "Anything else you'd like to tell your doctor?"

Patient replies: "Feeling a bit tired but okay"
  → save notes, mark step="done"
  → reply: "Thank you. Your doctor has been notified. Take care!"
  → notify doctor via SMS + email with full symptom summary
```

State is stored in `symptom_logs.chat_step` — no Redis needed.

---

## requirements.txt

```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
alembic
asyncpg
psycopg2-binary
pydantic-settings
scikit-learn
scikit-fuzzy
numpy
pandas
africastalking
joblib
python-dotenv
httpx
aiofiles
```

---

*RenalWatch — Built for Chuka University Hackathon*
*Smart CKD Outpatient Monitoring System*
*Not a diagnostic tool — a monitoring and alert system*
