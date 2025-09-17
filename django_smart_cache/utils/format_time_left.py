"""
Utilities for formatting time-related information.
"""

from datetime import timedelta
from typing import Union

from django.utils.translation import ngettext


def format_time_left(time_delta: timedelta | int | float) -> str:
    """
    Format a time delta into a human-readable string.

    Args:
        time_delta: A timedelta object, or seconds as int/float

    Returns:
        A formatted string like "2 days 3 hours" or "5 minutes"

    Examples:
        >>> from datetime import timedelta
        >>> format_time_left(timedelta(days=1, hours=2))
        '1 day 2 hours'
        >>> format_time_left(timedelta(seconds=90))
        '1 minute 30 seconds'
        >>> format_time_left(30)  # 30 seconds
        '30 seconds'
    """
    # Convert to timedelta if needed
    if isinstance(time_delta, (int, float)):
        time_delta = timedelta(seconds=time_delta)

    total_seconds = int(time_delta.total_seconds())

    # Handle edge cases
    if total_seconds <= 0:
        return "expired"

    if total_seconds < 60:
        return ngettext("%(count)d second", "%(count)d seconds", total_seconds) % {"count": total_seconds}

    # Time units in seconds (most efficient calculation)
    units = [
        ("year", 31536000),  # 365 * 24 * 60 * 60
        ("month", 2628000),  # ~30.44 * 24 * 60 * 60 (more accurate)
        ("week", 604800),  # 7 * 24 * 60 * 60
        ("day", 86400),  # 24 * 60 * 60
        ("hour", 3600),  # 60 * 60
        ("minute", 60),
        ("second", 1),
    ]

    result_parts = []
    remaining_seconds = total_seconds

    for unit_name, unit_seconds in units:
        if remaining_seconds >= unit_seconds:
            count = remaining_seconds // unit_seconds
            remaining_seconds %= unit_seconds

            # Use Django's ngettext for proper pluralization
            unit_display = ngettext(f"%(count)d {unit_name}", f"%(count)d {unit_name}s", count) % {"count": count}

            result_parts.append(unit_display)

            # Limit to 2 units for readability
            if len(result_parts) >= 2:
                break

    return " ".join(result_parts) if result_parts else "less than 1 minute"
