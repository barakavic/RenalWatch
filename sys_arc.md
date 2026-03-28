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