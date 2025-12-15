"""Tooling for Mark's demo availability calendar and CrewAI adapter."""

from __future__ import annotations

from datetime import date, timedelta

try:
    from crewai.tools import BaseTool
except Exception:  # noqa: BLE001 - allow importing pure helpers without CrewAI installed
    class BaseTool:  # type: ignore[override]
        """Fallback stub used for local tests when CrewAI is unavailable."""


AvailabilityMap = dict[str, str]


def _build_demo_availability(base_date: date | None = None) -> AvailabilityMap:
    first_day = base_date or (date.today() + timedelta(days=1))
    return {
        first_day.isoformat(): "busy all day",
        (first_day + timedelta(days=1)).isoformat(): "available from 11:00 to 15:00",
        (first_day + timedelta(days=2)).isoformat(): "available from 11:00 to 15:00",
        (first_day + timedelta(days=3)).isoformat(): "available all day",
        (first_day + timedelta(days=4)).isoformat(): "busy all day",
    }


FAKE_AVAILABILITY: AvailabilityMap = _build_demo_availability()


def get_availability(date_str: str) -> dict[str, str]:
    """Return Mark's availability for an ISO date from the demo calendar."""
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
            "message": f"On {normalized_date}, Mark is {availability}.",
        }

    return {
        "status": "input_required",
        "message": (
            f"No availability is recorded for Mark on {normalized_date}. "
            "Please ask about another date."
        ),
    }


class AvailabilityTool(BaseTool):
    name: str = "Calendar Availability Checker"
    description: str = "Checks Mark's availability for a given date (YYYY-MM-DD)."

    def _run(self, date: str) -> str:
        return get_availability(date)["message"]
