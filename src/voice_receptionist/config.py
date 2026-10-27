"""Load and validate receptionist configuration before it reaches an API."""

from __future__ import annotations

import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
PRACTICE_TYPES = {"dental", "med_spa"}
BOOKING_MODES = {"request_only", "confirmed_booking"}
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CLOCK = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class ConfigError(ValueError):
    """Raised when a configuration could make an unsafe or invalid agent."""


def _required(mapping: dict, key: str, where: str):
    value = mapping.get(key)
    if value in (None, "", []):
        raise ConfigError(f"{where}.{key} is required")
    return value


def _validate_hours(hours: dict, where: str) -> None:
    if not isinstance(hours, dict):
        raise ConfigError(f"{where}.hours must be an object")
    unknown = set(hours) - set(DAYS)
    if unknown:
        raise ConfigError(f"{where}.hours has unknown days: {', '.join(sorted(unknown))}")
    for day in DAYS:
        periods = hours.get(day, [])
        if not isinstance(periods, list):
            raise ConfigError(f"{where}.hours.{day} must be a list")
        previous_end = "00:00"
        for period in periods:
            if not isinstance(period, list) or len(period) != 2:
                raise ConfigError(f"{where}.hours.{day} periods must be [open, close]")
            start, end = period
            if not isinstance(start, str) or not isinstance(end, str) or not _CLOCK.match(start) or not _CLOCK.match(end):
                raise ConfigError(f"{where}.hours.{day} uses invalid 24 hour time")
            if start >= end:
                raise ConfigError(f"{where}.hours.{day} must open before it closes")
            if start < previous_end:
                raise ConfigError(f"{where}.hours.{day} periods overlap")
            previous_end = end


def _validate_location(location: dict, index: int) -> None:
    where = f"locations[{index}]"
    for key in ("id", "practice_name", "practice_type", "city", "state", "timezone", "agent_name", "voice_id"):
        _required(location, key, where)
    if not _SLUG.match(location["id"]):
        raise ConfigError(f"{where}.id must be a lowercase slug")
    if location["practice_type"] not in PRACTICE_TYPES:
        raise ConfigError(f"{where}.practice_type must be dental or med_spa")
    try:
        ZoneInfo(location["timezone"])
    except ZoneInfoNotFoundError as exc:
        raise ConfigError(f"{where}.timezone is not recognized") from exc
    _validate_hours(_required(location, "hours", where), where)

    services = _required(location, "services", where)
    if not isinstance(services, list) or not all(isinstance(item, str) and item.strip() for item in services):
        raise ConfigError(f"{where}.services must contain nonempty strings")

    booking = _required(location, "booking", where)
    if not isinstance(booking, dict):
        raise ConfigError(f"{where}.booking must be an object")
    if booking.get("mode") not in BOOKING_MODES:
        raise ConfigError(f"{where}.booking.mode must be request_only or confirmed_booking")
    for key in ("duration_minutes", "buffer_minutes", "minimum_notice_hours", "offer_count"):
        value = booking.get(key)
        if not isinstance(value, int) or value < 0:
            raise ConfigError(f"{where}.booking.{key} must be a nonnegative integer")
    if booking["duration_minutes"] == 0 or booking["offer_count"] == 0:
        raise ConfigError(f"{where}.booking duration and offer_count must be positive")

    retell = _required(location, "retell", where)
    if not isinstance(retell, dict):
        raise ConfigError(f"{where}.retell must be an object")
    for key in ("agent_id_env", "llm_id_env"):
        env_name = _required(retell, key, f"{where}.retell")
        if not re.match(r"^[A-Z][A-Z0-9_]+$", env_name):
            raise ConfigError(f"{where}.retell.{key} must be an environment variable name")


def load_config(path: str | Path) -> dict:
    """Read a JSON config and fail closed on missing or malformed safety fields."""
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"config not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {source}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("config root must be an object")
    if data.get("schema_version") != 1:
        raise ConfigError("schema_version must be 1")
    retell = _required(data, "retell", "config")
    if not isinstance(retell, dict) or not isinstance(retell.get("model"), str):
        raise ConfigError("config.retell.model is required")
    locations = _required(data, "locations", "config")
    if not isinstance(locations, list):
        raise ConfigError("config.locations must be a list")
    seen: set[str] = set()
    for index, location in enumerate(locations):
        if not isinstance(location, dict):
            raise ConfigError(f"locations[{index}] must be an object")
        _validate_location(location, index)
        if location["id"] in seen:
            raise ConfigError(f"duplicate location id: {location['id']}")
        seen.add(location["id"])
    return data
