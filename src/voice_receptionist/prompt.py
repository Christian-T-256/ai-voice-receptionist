"""Render a deterministic, safety-first voice agent prompt."""

from __future__ import annotations

import re
from pathlib import Path

from .config import DAYS

DEFAULT_TEMPLATE = Path(__file__).resolve().parents[2] / "prompts" / "receptionist.md"
DAY_LABELS = {day: day.title() for day in DAYS}


def format_hours(hours: dict) -> str:
    lines: list[str] = []
    for day in DAYS:
        periods = hours.get(day, [])
        value = ", ".join(f"{start} to {end}" for start, end in periods) if periods else "closed"
        lines.append(f"- {DAY_LABELS[day]}: {value}")
    return "\n".join(lines)


def booking_instruction(booking: dict) -> str:
    details = (
        f"Appointments are {booking['duration_minutes']} minutes with a {booking['buffer_minutes']} minute buffer. "
        f"Respect at least {booking['minimum_notice_hours']} hours of notice. "
        f"Offer {booking['offer_count']} specific options inside the listed hours."
    )
    if booking["mode"] == "request_only":
        return details + " This workflow records appointment requests only. Never say an appointment is confirmed. Tell the caller the clinic will confirm it."
    return details + " Confirm a slot only after the connected scheduling tool returns success."


def render_prompt(location: dict, model_name: str, template_path: str | Path = DEFAULT_TEMPLATE) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    is_dental = location["practice_type"] == "dental"
    replacements = {
        "AGENT_NAME": location["agent_name"],
        "PRACTICE_NAME": location["practice_name"],
        "PRACTICE_TYPE": "dental clinic" if is_dental else "medical spa",
        "CITY": location["city"],
        "STATE": location["state"],
        "TIMEZONE": location["timezone"],
        "MODEL_NAME": model_name,
        "HOURS": format_hours(location["hours"]),
        "SERVICES": "\n".join(f"- {service}" for service in location["services"]),
        "BOOKING_RULES": booking_instruction(location["booking"]),
        "INSURANCE_NOTE": location["insurance_note"],
        "EMERGENCY_EXAMPLES": (
            "heavy bleeding, facial trauma, or swelling that affects breathing"
            if is_dental
            else "trouble breathing, severe swelling, or a possible allergic reaction"
        ),
    }
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", rendered)))
    if unresolved:
        raise ValueError(f"unresolved prompt variables: {', '.join(unresolved)}")
    return rendered.strip()


def begin_message(location: dict) -> str:
    if location["practice_type"] == "dental":
        question = "How can I help you today?"
    else:
        question = "Are you calling about an appointment or an existing visit?"
    return f"Thank you for calling {location['practice_name']}. This is {location['agent_name']}. {question}"
