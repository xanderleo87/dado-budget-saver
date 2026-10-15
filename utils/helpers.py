"""Utility helpers for date parsing, currency formatting, and fuzzy matching."""

from datetime import datetime, timedelta, timezone
import re
from utils.constants import CURRENCY_SYMBOL

# Asia/Manila timezone (UTC+8, no DST)
PH_TZ = timezone(timedelta(hours=8))


def now_ph() -> datetime:
    """Return current datetime in Asia/Manila timezone."""
    return datetime.now(PH_TZ)


def format_currency(amount: float) -> str:
    """Format amount as ₱1,234.56"""
    return f"{CURRENCY_SYMBOL}{amount:,.2f}"


def parse_relative_date(text: str) -> str | None:
    """Parse relative date expressions to YYYY-MM-DD."""
    text = text.lower().strip()
    today = now_ph()

    if text in ("today", "now"):
        return today.strftime("%Y-%m-%d")
    if text == "yesterday":
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")

    days_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }

    match = re.match(r"last\s+(\w+)", text)
    if match:
        day_name = match.group(1)
        if day_name in days_map:
            target = days_map[day_name]
            current = today.weekday()
            diff = (current - target) % 7
            if diff == 0:
                diff = 7
            return (today - timedelta(days=diff)).strftime("%Y-%m-%d")

    match = re.match(r"(\d+)\s+days?\s+ago", text)
    if match:
        days = int(match.group(1))
        return (today - timedelta(days=days)).strftime("%Y-%m-%d")

    return None


def today_str() -> str:
    """Return today's date as YYYY-MM-DD in Asia/Manila timezone."""
    return now_ph().strftime("%Y-%m-%d")


def now_str() -> str:
    """Return current datetime as YYYY-MM-DD HH:MM in Asia/Manila timezone."""
    return now_ph().strftime("%Y-%m-%d %H:%M")


def current_month_year() -> str:
    """Return current month as YYYY-MM in Asia/Manila timezone."""
    return now_ph().strftime("%Y-%m")


def month_display(month_year: str) -> str:
    """Convert YYYY-MM to 'February 2026' display format."""
    try:
        dt = datetime.strptime(month_year, "%Y-%m")
        return dt.strftime("%B %Y")
    except ValueError:
        return month_year


def fuzzy_match(query: str, choices: list[str], threshold: int = 70) -> str | None:
    """Fuzzy match a query against a list of choices. Returns best match or None."""
    try:
        from thefuzz import fuzz, process
        result = process.extractOne(query, choices, scorer=fuzz.token_sort_ratio)
        if result and result[1] >= threshold:
            return result[0]
    except ImportError:
        # Fallback: simple case-insensitive contains
        query_lower = query.lower()
        for choice in choices:
            if query_lower in choice.lower() or choice.lower() in query_lower:
                return choice
    return None
