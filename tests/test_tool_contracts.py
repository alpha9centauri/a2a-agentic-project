"""Unit tests for local scheduling tools used by the demo agents."""

from __future__ import annotations

import unittest

import jeff_agent.tools as jeff_tools
import mark_agent.tools as mark_tools
from elon_agent.elon import tools as court_tools


class AvailabilityToolTests(unittest.TestCase):
    def test_jeff_tool_requires_iso_format(self) -> None:
        result = jeff_tools.get_availability("tomorrow")
        self.assertEqual(result["status"], "error")
        self.assertIn("YYYY-MM-DD", result["message"])

    def test_mark_tool_mentions_mark(self) -> None:
        demo_date = next(iter(mark_tools.FAKE_AVAILABILITY.keys()))
        result = mark_tools.get_availability(demo_date)
        self.assertEqual(result["status"], "completed")
        self.assertIn("Mark is", result["message"])


class CourtToolTests(unittest.TestCase):
    def setUp(self) -> None:
        court_tools.reset_court_schedule()

    def test_list_court_availability_returns_expected_keys(self) -> None:
        demo_date = next(iter(court_tools.COURT_SCHEDULE.keys()))
        result = court_tools.list_court_availabilities(demo_date)
        self.assertEqual(result["status"], "success")
        self.assertIn("available_slots", result)
        self.assertIn("blocked_slots", result)
        self.assertIn("booked_slots", result)

    def test_booking_updates_slot_state(self) -> None:
        demo_date = next(iter(court_tools.COURT_SCHEDULE.keys()))
        available_slots = [
            slot
            for slot, state in court_tools.COURT_SCHEDULE[demo_date].items()
            if state == court_tools.AVAILABLE
        ]
        self.assertTrue(available_slots, "Expected at least one available demo slot")

        selected_slot = available_slots[0]
        next_hour_for_slot = {
            "08:00": "09:00",
            "09:00": "10:00",
            "10:00": "11:00",
            "11:00": "12:00",
        }
        booking_result = court_tools.book_badminton_court(
            requested_date=demo_date,
            start_time=selected_slot,
            end_time=next_hour_for_slot.get(selected_slot, "23:59"),
            reservation_name="Team A",
        )

        self.assertEqual(booking_result["status"], "success")
        self.assertEqual(court_tools.COURT_SCHEDULE[demo_date][selected_slot], "Team A")


if __name__ == "__main__":
    unittest.main()
