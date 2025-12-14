"""Court scheduling tools used by the host coordinator agent."""

from __future__ import annotations

from datetime import date, datetime, timedelta

AVAILABLE = "available"
MAINTENANCE = "maintenance"
DEFAULT_SLOT_TIMES = ("08:00", "09:00", "10:00", "11:00")

CourtSchedule = dict[str, dict[str, str]]


def _build_initial_schedule(base_date: date | None = None) -> CourtSchedule:
    """Build a small in-memory demo schedule relative to the current date."""
    first_day = base_date or (date.today() + timedelta(days=1))
    schedule: CourtSchedule = {}

    day_1 = first_day.isoformat()
    day_2 = (first_day + timedelta(days=1)).isoformat()
    day_3 = (first_day + timedelta(days=2)).isoformat()

    schedule[day_1] = {
        "08:00": AVAILABLE,
        "09:00": AVAILABLE,
        "10:00": MAINTENANCE,
        "11:00": AVAILABLE,
    }
    schedule[day_2] = {
        "08:00": "morning-club",
        "09:00": AVAILABLE,
        "10:00": AVAILABLE,
        "11:00": AVAILABLE,
    }
    schedule[day_3] = {slot: AVAILABLE for slot in DEFAULT_SLOT_TIMES}
    return schedule


COURT_SCHEDULE: CourtSchedule = _build_initial_schedule()


def reset_court_schedule() -> None:
    """Reset the in-memory schedule to its demo default state."""
    global COURT_SCHEDULE
    COURT_SCHEDULE = _build_initial_schedule()


def _parse_time_label(value: str) -> datetime:
    return datetime.strptime(value, "%H:%M")


def list_court_availabilities(requested_date: str) -> dict[str, object]:
    """List available, blocked, and booked slots for a given ISO date."""
    if requested_date not in COURT_SCHEDULE:
        return {
            "status": "error",
            "message": (
                f"No court schedule found for {requested_date}. "
                f"Available demo dates: {sorted(COURT_SCHEDULE.keys())}"
            ),
            "available_slots": [],
            "blocked_slots": {},
            "booked_slots": {},
        }

    daily_schedule = COURT_SCHEDULE[requested_date]
    available_slots = [slot for slot, state in daily_schedule.items() if state == AVAILABLE]
    blocked_slots = {slot: state for slot, state in daily_schedule.items() if state == MAINTENANCE}
    booked_slots = {
        slot: state
        for slot, state in daily_schedule.items()
        if state not in {AVAILABLE, MAINTENANCE}
    }

    return {
        "status": "success",
        "message": f"Court schedule for {requested_date}.",
        "available_slots": available_slots,
        "blocked_slots": blocked_slots,
        "booked_slots": booked_slots,
    }


def book_badminton_court(
    requested_date: str,
    start_time: str,
    end_time: str,
    reservation_name: str,
) -> dict[str, str]:
    """Book a single court slot in the in-memory demo schedule."""
    if requested_date not in COURT_SCHEDULE:
        return {
            "status": "error",
            "message": (
                f"No court schedule found for {requested_date}. "
                f"Available demo dates: {sorted(COURT_SCHEDULE.keys())}"
            ),
        }

    try:
        start_label = _parse_time_label(start_time)
        end_label = _parse_time_label(end_time)
    except ValueError:
        return {
            "status": "error",
            "message": "Time must be provided in 24-hour HH:MM format.",
        }

    if end_label <= start_label:
        return {
            "status": "error",
            "message": "end_time must be later than start_time.",
        }

    daily_schedule = COURT_SCHEDULE[requested_date]
    if start_time not in daily_schedule:
        valid_slots = ", ".join(sorted(daily_schedule.keys()))
        return {
            "status": "error",
            "message": f"Invalid start_time '{start_time}'. Valid slots: {valid_slots}.",
        }

    current_state = daily_schedule[start_time]
    if current_state != AVAILABLE:
        return {
            "status": "error",
            "message": (
                f"Slot {start_time} on {requested_date} is unavailable "
                f"(current state: {current_state})."
            ),
        }

    cleaned_name = reservation_name.strip() or "Badminton Group"
    daily_schedule[start_time] = cleaned_name
    return {
        "status": "success",
        "message": f"Booked {requested_date} {start_time}-{end_time} for {cleaned_name}.",
    }
