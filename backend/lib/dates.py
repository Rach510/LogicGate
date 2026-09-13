"""Server-side date helpers. The pod clock is UTC — anchor "today" here, never in the browser."""

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def today_iso(tz: str | None = None) -> str:
    """Today's date as YYYY-MM-DD in `tz` (default: APP_TZ env, else UTC)."""
    zone = tz or os.environ.get("APP_TZ", "UTC")
    return datetime.now(ZoneInfo(zone)).strftime("%Y-%m-%d")


def relative_label(moment: datetime) -> str:
    """"Updated 12 min ago"-style label for a UTC-aware datetime, used on Project.updated."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - moment
    seconds = max(delta.total_seconds(), 0)
    if seconds < 60:
        return "Updated just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"Updated {minutes} min ago"
    hours = int(minutes // 60)
    if hours < 24:
        return f"Updated {hours} hour{'s' if hours != 1 else ''} ago"
    days = int(hours // 24)
    if days == 1:
        return "Updated yesterday"
    if days < 7:
        return f"Updated {days} days ago"
    weeks = int(days // 7)
    if weeks < 5:
        return f"Updated {weeks} week{'s' if weeks != 1 else ''} ago"
    return f"Updated on {moment.strftime('%d %b %Y')}"
