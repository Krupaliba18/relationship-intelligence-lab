"""Small, transparent, rule-based proof of concept, not an AI model."""

from __future__ import annotations
from calendar import monthrange
from datetime import date, timedelta
import re


def add_calendar_months(day: date, count: int) -> date:
    year = day.year + (day.month - 1 + count) // 12
    month = (day.month - 1 + count) % 12 + 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


def next_weekday(day: date) -> date:
    if day.weekday() >= 5:
        return day + timedelta(days=7 - day.weekday())
    return day


def recommend(notes: str, interaction_date: date, shift_weekends: bool = True) -> dict:
    """Interpret a limited selection of phrases; external actions require approval."""
    text = notes.lower()
    if re.search(r"\b(do not contact|don't contact|never contact|unsubscribe|opt[ -]?out)\b", text):
        return {"status": "Do not contact", "requested_date": None,
                "suggested_date": None, "reason": "Contact restriction detected",
                "action": "Do not schedule outreach", "requires_approval": True}

    status = "On hold" if re.search(r"\b(another vendor|existing vendor|on hold|not interested right now|not planning to change)\b", text) else "Engaged"
    matches = list(re.finditer(r"\b(?:after|in)\s+(\d+)\s+(days?|weeks?|months?|years?)\b", text))
    if len(matches) > 1:
        return {"status": status, "requested_date": None, "suggested_date": None,
                "reason": "Multiple time expressions; user must choose", "action": "Clarify timing",
                "requires_approval": True}

    if len(matches) == 1:
        number = int(matches[0].group(1))
        unit = matches[0].group(2)
        if number < 1 or number > 3650:
            raise ValueError("Time interval out of supported range")
        if unit.startswith("day"):
            requested = interaction_date + timedelta(days=number)
        elif unit.startswith("week"):
            requested = interaction_date + timedelta(weeks=number)
        elif unit.startswith("month"):
            requested = add_calendar_months(interaction_date, number)
        else:
            requested = add_calendar_months(interaction_date, number * 12)
        return {"status": status, "requested_date": requested.isoformat(),
                "suggested_date": (next_weekday(requested) if shift_weekends else requested).isoformat(),
                "reason": f"Interpreted '{matches[0].group(0)}' from {interaction_date.isoformat()}",
                "action": "Prepare research brief before approved reconnection" if status == "On hold" else "Review next action",
                "requires_approval": True}

    if re.search(r"\btomorrow\b", text):
        requested = interaction_date + timedelta(days=1)
        return {"status": status, "requested_date": requested.isoformat(),
                "suggested_date": (next_weekday(requested) if shift_weekends else requested).isoformat(),
                "reason": "Interpreted 'tomorrow'", "action": "Review requested action",
                "requires_approval": True}

    return {"status": status, "requested_date": None, "suggested_date": None,
            "reason": "No supported explicit timeframe detected", "action": "Ask user to select a date",
            "requires_approval": True}


if __name__ == "__main__":
    sample = "We're with another vendor. Please reconnect after 3 months."
    print(recommend(sample, date(2026, 10, 15)))
