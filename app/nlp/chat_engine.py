import json
import logging
import re
from typing import Any

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)

_SESSIONS: dict[str, list[dict[str, str]]] = {}

CHAT_PROMPT = """You are RenalWatch, a warm friendly health assistant for CKD patients.
Your job is to collect 4 symptom ratings through natural conversation:
1. Fatigue level (1-10)
2. Pain level (1-10)
3. Leg/ankle swelling (1-10)
4. Nausea level (1-10)

Ask ONE question at a time. Be brief and empathetic.
Do not repeat the same question if the patient already answered it.
If the patient mentions a symptom naturally, follow up on the most useful missing detail.
When you have all 4 ratings, say thank you and that the doctor will be notified."""

EXTRACT_PROMPT = """Read this conversation and extract symptom values.
Return ONLY a JSON object, nothing else.
If a value was not mentioned, use null.
Set complete to true only if all 4 values were collected.

JSON format:
{
  "fatigue": null,
  "pain_level": null,
  "swelling": null,
  "nausea": null,
  "notes": "",
  "complete": false
}"""


def is_model_available() -> bool:
    return bool(settings.openrouter_api_key)


def warm_chat_model() -> None:
    logger.info("Chatbot OpenRouter mode: %s", "enabled" if is_model_available() else "disabled")


def reset_chat_session(phone: str) -> None:
    _SESSIONS.pop(phone, None)


def start_model_checkin(patient_name: str, phone: str) -> str:
    _SESSIONS[phone] = []
    return (
        f"Hi {patient_name}, I am checking in on how you feel today. "
        "Tell me in your own words what symptoms or concerns you have noticed."
    )


def generate_model_followup(patient_name: str, phone: str, user_message: str) -> dict[str, Any]:
    history = _SESSIONS.setdefault(phone, [])
    history.append({"role": "user", "content": user_message})

    if not is_model_available():
        return _fallback_followup(phone, user_message)

    try:
        reply = _call_openrouter([{"role": "system", "content": CHAT_PROMPT}, *history])
        history.append({"role": "assistant", "content": reply})
        extracted = extract_values(history)
        return {
            "reply": reply,
            "summary": extracted.get("notes") or f"Patient reported: {user_message}",
            "symptom_ratings": {
                "fatigue": extracted.get("fatigue"),
                "pain": extracted.get("pain_level"),
                "swelling": extracted.get("swelling"),
                "nausea": extracted.get("nausea"),
            },
            "symptoms": [],
            "done": bool(extracted.get("complete")),
            "escalate": _has_emergency_signal(user_message),
        }
    except Exception as exc:
        logger.warning("OpenRouter chatbot failed, using local fallback: %s", exc)
        return _fallback_followup(phone, user_message)


def extract_values(history: list[dict[str, str]]) -> dict[str, Any]:
    conversation_text = "\n".join(
        [f"{'Patient' if item['role'] == 'user' else 'RenalWatch'}: {item['content']}" for item in history]
    )
    try:
        raw = _call_openrouter(
            [
                {"role": "system", "content": EXTRACT_PROMPT},
                {"role": "user", "content": conversation_text},
            ]
        )
        clean = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(clean)
        return {
            "fatigue": _coerce_rating(data.get("fatigue")),
            "pain_level": _coerce_rating(data.get("pain_level")),
            "swelling": _coerce_rating(data.get("swelling")),
            "nausea": _coerce_rating(data.get("nausea")),
            "notes": (data.get("notes") or "").strip(),
            "complete": bool(data.get("complete")),
        }
    except Exception as exc:
        logger.warning("OpenRouter extraction failed, using heuristic extraction: %s", exc)
        return _heuristic_extract(conversation_text)


def apply_symptom_ratings(log, symptom_ratings: dict[str, Any]) -> None:
    fatigue = _coerce_rating(symptom_ratings.get("fatigue"))
    pain = _coerce_rating(symptom_ratings.get("pain"))
    swelling = _coerce_rating(symptom_ratings.get("swelling"))
    nausea = _coerce_rating(symptom_ratings.get("nausea"))

    if fatigue is not None:
        log.fatigue = fatigue
    if pain is not None:
        log.pain_level = pain
    if swelling is not None:
        log.swelling = swelling
    if nausea is not None:
        log.nausea = nausea


def _call_openrouter(messages: list[dict[str, str]]) -> str:
    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://renalwatch.app",
            "X-Title": "RenalWatch",
        },
        json={
            "model": settings.openrouter_model,
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.5,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _fallback_followup(phone: str, user_message: str) -> dict[str, Any]:
    history = _SESSIONS.setdefault(phone, [])
    conversation_text = "\n".join(
        [f"{'Patient' if item['role'] == 'user' else 'RenalWatch'}: {item['content']}" for item in history]
    )
    extracted = _heuristic_extract(conversation_text)
    reply = _next_question(extracted, user_message)
    history.append({"role": "assistant", "content": reply})
    return {
        "reply": reply,
        "summary": extracted.get("notes") or f"Patient reported: {user_message}",
        "symptom_ratings": {
            "fatigue": extracted.get("fatigue"),
            "pain": extracted.get("pain_level"),
            "swelling": extracted.get("swelling"),
            "nausea": extracted.get("nausea"),
        },
        "symptoms": [],
        "done": bool(extracted.get("complete")),
        "escalate": _has_emergency_signal(user_message),
    }


def _heuristic_extract(conversation_text: str) -> dict[str, Any]:
    text = conversation_text.lower()
    lines = [line.strip() for line in conversation_text.splitlines() if line.strip().lower().startswith("patient:")]

    values = {
        "fatigue": None,
        "pain_level": None,
        "swelling": None,
        "nausea": None,
        "notes": "",
        "complete": False,
    }

    last_nonempty = ""
    for line in lines:
        content = line.split(":", 1)[1].strip()
        if content:
            last_nonempty = content

        number_match = re.search(r"\b10\b|\b[1-9]\b", content.lower())
        rating = int(number_match.group()) if number_match else None

        if any(word in content.lower() for word in ["weak", "weakness", "tired", "fatigue", "energy"]):
            values["fatigue"] = rating if rating is not None else values["fatigue"]
        if any(word in content.lower() for word in ["pain", "hurt", "ache", "aching", "sore"]):
            values["pain_level"] = rating if rating is not None else values["pain_level"]
        if any(word in content.lower() for word in ["swelling", "swollen", "ankle", "ankles", "leg", "legs"]):
            values["swelling"] = rating if rating is not None else values["swelling"]
        if any(word in content.lower() for word in ["nausea", "nauseous", "vomit", "vomiting"]):
            values["nausea"] = rating if rating is not None else values["nausea"]

    if last_nonempty:
        values["notes"] = f"Patient reported: {last_nonempty}"

    values["complete"] = all(values[key] is not None for key in ["fatigue", "pain_level", "swelling", "nausea"])
    return values


def _next_question(extracted: dict[str, Any], user_message: str) -> str:
    if _has_emergency_signal(user_message):
        return "Your symptoms may be urgent. Are you having chest pain or trouble breathing right now?"
    if extracted.get("fatigue") is None:
        return "Thank you. What is your fatigue or low energy level today on a scale of 1 to 10?"
    if extracted.get("pain_level") is None:
        return "Thank you. What is your pain level today on a scale of 1 to 10?"
    if extracted.get("swelling") is None:
        return "Thank you. How much leg or ankle swelling are you having today on a scale of 1 to 10?"
    if extracted.get("nausea") is None:
        return "Thank you. What is your nausea level today on a scale of 1 to 10?"
    return "Thank you. Your symptoms have been recorded and your doctor will be notified."


def _has_emergency_signal(user_message: str) -> bool:
    normalized = user_message.lower()
    emergency_keywords = {
        "chest pain",
        "shortness of breath",
        "cannot breathe",
        "can't breathe",
        "fainting",
        "passed out",
    }
    return any(keyword in normalized for keyword in emergency_keywords)


def _coerce_rating(value: Any) -> int | None:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None
    return numeric if 1 <= numeric <= 10 else None
