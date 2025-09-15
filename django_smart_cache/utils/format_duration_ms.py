from typing import Union


def format_duration_ms(duration_ms: Union[int, float]) -> str:
    """
    Format duration in milliseconds to a human-readable string.

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        Formatted duration string

    Examples:
        >>> format_duration_ms(1500)
        '1.5s'
        >>> format_duration_ms(500)
        '500ms'
        >>> format_duration_ms(65000)
        '1m 5s'
    """
    if duration_ms < 1000:
        return f"{int(duration_ms)}ms"

    total_seconds = duration_ms / 1000

    if total_seconds < 60:
        if total_seconds == int(total_seconds):
            return f"{int(total_seconds)}s"
        return f"{total_seconds:.1f}s"

    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)

    if seconds == 0:
        return f"{minutes}m"

    return f"{minutes}m {seconds}s"
