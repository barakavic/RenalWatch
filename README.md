# RenalWatch
A smart monitoring system for CKD patients that can be extensible to other BP reliant diseases

## Demo Integrations

RenalWatch supports a demo-ready external integration path for:

- Africa's Talking SMS
- WhatsApp chatbot webhook with SMS transport fallback
- Gmail SMTP email delivery
- ZFit / fitPro smartwatch ingestion through the ADB worker

### Required environment variables

Copy `.env.example` to `.env` and populate:

- `AT_API_KEY`
- `AT_USERNAME`
- `AT_SENDER_ID` (optional)
- `SMTP_EMAIL`
- `SMTP_PASSWORD`
- `DOCTOR_PHONE`
- `DOCTOR_EMAIL`

### Demo behavior

- `POST /chatbot/webhook` accepts Africa's Talking-style form payloads.
- `GET /chatbot/webhook` returns a readiness response for webhook setup checks.
- If WhatsApp outbound is not fully provisioned, chatbot replies can fall back to SMS transport when `WHATSAPP_DEMO_FALLBACK_TO_SMS=true`.
- The ADB worker reads the latest ZFit blood pressure entry and posts it to `/readings/`.

### Running the demo stack

```bash
docker compose up -d
docker compose --profile workers up -d adb-worker scheduler
```
