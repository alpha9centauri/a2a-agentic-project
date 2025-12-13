"""Tooling for Jeff's demo availability calendar."""

from __future__ import annotations

from datetime import date, timedelta

AvailabilityMap = dict[str, str]


def _build_demo_availability(base_date: date | None = None) -> AvailabilityMap:
    first_day = base_date or (date.today() + timedelta(days=1))
    return {
        first_day.isoformat(): "available from 16:00 to 18:00",
        (first_day + timedelta(days=1)).isoformat(): "available from 10:00 to 12:00",
        (first_day + timedelta(days=2)).isoformat(): "available from 11:00 to 12:00",
        (first_day + timedelta(days=3)).isoformat(): "busy from 13:00 to 17:00",
        (first_day + timedelta(days=4)).isoformat(): "available all day",
    }


FAKE_AVAILABILITY: AvailabilityMap = _build_demo_availability()


def get_availability(date_str: str) -> dict[str, str]:
    """Return Jeff's availability for an ISO date from the demo calendar."""
    if not date_str or not date_str.strip():
        return {"status": "error", "message": "No date provided. Use YYYY-MM-DD."}

    normalized_date = date_str.strip()
    try:
        date.fromisoformat(normalized_date)
    except ValueError:
        return {
            "status": "error",
            "message": f"Invalid date '{date_str}'. Use ISO format YYYY-MM-DD.",
        }

    availability = FAKE_AVAILABILITY.get(normalized_date)
    if availability:
        return {
            "status": "completed",
            "message": f"On {normalized_date}, Jeff is {availability}.",
        }

    return {
        "status": "input_required",
        "message": (
            f"No availability is recorded for Jeff on {normalized_date}. "
            "Please ask about another date."
        ),
    }
