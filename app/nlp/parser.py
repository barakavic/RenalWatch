import re


GREETING_WORDS = {
    "hello",
    "hi",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "habari",
    "sasa",
}

HELP_WORDS = {
    "help",
    "what",
    "how",
    "confused",
    "don't understand",
    "dont understand",
    "repeat",
    "explain",
}

YES_WORDS = {"yes", "yeah", "yep", "sure", "okay", "ok"}
NO_WORDS = {"no", "nope", "not really"}


def parse_chat_message(text: str) -> dict:
    normalized = " ".join(text.strip().lower().split())
    number_match = re.search(r"\b10\b|\b[1-9]\b", normalized)
    number = int(number_match.group()) if number_match else None

    return {
        "raw": text,
        "normalized": normalized,
        "is_greeting": normalized in GREETING_WORDS or any(word in normalized for word in GREETING_WORDS),
        "is_help": any(word in normalized for word in HELP_WORDS),
        "is_affirmative": normalized in YES_WORDS,
        "is_negative": normalized in NO_WORDS,
        "number": number,
        "has_free_text": bool(normalized and number is None),
    }
