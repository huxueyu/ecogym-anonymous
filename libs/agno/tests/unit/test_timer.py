import pytest

from agno.tools.timer import TimerTools


class TestTimerTools:
    def test_advance_day_initializes_and_increments(self):
        timer = TimerTools()
        session_state = {}

        msg1 = timer.advance_day(session_state)
        assert session_state["day"] == 1
        assert session_state["day_history"] == [1]
        assert "Current day: 1" in msg1

        msg2 = timer.advance_day(session_state)
        assert session_state["day"] == 2
        assert session_state["day_history"] == [1, 2]
        assert "Current day: 2" in msg2

    def test_advance_day_multiple_calls_from_existing_day(self):
        timer = TimerTools()
        session_state = {"day": 5, "day_history": [1, 2, 3, 4, 5]}

        timer.advance_day(session_state)
        assert session_state["day"] == 6
        assert session_state["day_history"][-1] == 6

        timer.advance_day(session_state)
        assert session_state["day"] == 7
        assert session_state["day_history"][-2:] == [6, 7]

    def test_advance_day_handles_non_int_day(self):
        timer = TimerTools()
        session_state = {"day": "not-an-int"}

        timer.advance_day(session_state)
        # Non-int should be re-initialized to 0, then +1
        assert session_state["day"] == 1
        assert session_state["day_history"] == [1]


