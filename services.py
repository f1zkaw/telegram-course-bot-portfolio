"""Pure functions that can be tested without Telegram or live credentials."""
from datetime import datetime, timedelta, timezone


def daily_available(last_iso: str | None, now: datetime | None = None) -> tuple[bool, timedelta]:
    if now is None:
        now = datetime.now(timezone.utc)
    if not last_iso:
        return True, timedelta(0)
    previous = datetime.fromisoformat(last_iso)
    if previous.tzinfo is None:
        previous = previous.replace(tzinfo=timezone.utc)
    remaining = timedelta(hours=24) - (now - previous)
    return (remaining <= timedelta(0), max(timedelta(0), remaining))


def valid_checkout(payload: str, user_id: int,
                   total_amount: int, currency: str,
                   expected_amount: int, expected_currency: str) -> bool:
    return (payload == f"demo_course_{user_id}"
            and total_amount == expected_amount
            and currency == expected_currency)
