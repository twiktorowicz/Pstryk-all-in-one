"""Helpers for reusing cached pricing data across the midnight rollover."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

try:
    from homeassistant.util import dt as dt_util
except ImportError:  # pragma: no cover - Home Assistant not available in isolated unit tests
    dt_util = None


def _parse_frame_start(start_value: Any) -> Optional[datetime]:
    """Parse an ISO datetime string from a pricing frame."""
    if not isinstance(start_value, str) or not start_value:
        return None

    normalized = start_value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _as_local_date(dt_value: datetime) -> date:
    """Convert aware datetimes to the Home Assistant local date when possible."""
    if dt_value.tzinfo is None:
        return dt_value.date()

    if dt_util is not None:
        return dt_util.as_local(dt_value).date()

    return dt_value.astimezone().date()


def has_frames_for_date(response_data: Optional[dict[str, Any]], expected_date: date) -> bool:
    """Return True when the pricing response contains frames for the expected local date."""
    if not isinstance(response_data, dict):
        return False

    frames = response_data.get("frames")
    if not isinstance(frames, list) or not frames:
        return False

    first_frame = frames[0]
    if not isinstance(first_frame, dict):
        return False

    start_dt = _parse_frame_start(first_frame.get("start"))
    if start_dt is None:
        return False

    return _as_local_date(start_dt) == expected_date


def has_complete_price_data(response_data: Optional[dict], expected_hours: int = 24) -> bool:
    """Sprawdza czy dane cenowe są kompletne (wszystkie godziny mają cenę).

    Ramki z price_gross=None oznaczają godziny jeszcze nieopublikowane.
    Ramki z price_gross=0.0 to legitymalnie zerowe ceny (np. nadwyżka solarna).
    """
    if not response_data or not isinstance(response_data.get("frames"), list):
        return False
    frames = response_data["frames"]
    if len(frames) < expected_hours:
        return False
    with_price = sum(1 for f in frames if f.get("price_gross") is not None)
    return with_price >= expected_hours


def select_today_pricing_response(
    api_response: Optional[dict[str, Any]],
    cached_today: Optional[dict[str, Any]],
    promotable_tomorrow: Optional[dict[str, Any]],
    expected_date: date,
) -> tuple[dict[str, Any], bool]:
    """Pick the best response for today's pricing.

    Priority: fresh API data > promoted tomorrow cache > existing today cache.
    """
    if has_frames_for_date(api_response, expected_date):
        return api_response or {}, True

    if has_frames_for_date(promotable_tomorrow, expected_date):
        return promotable_tomorrow or {}, True

    if isinstance(cached_today, dict):
        return cached_today, False

    return {}, False


def has_meaningful_price_data(response_data: Optional[dict]) -> bool:
    """Return True when the response has at least one frame with non-zero price_gross."""
    if not response_data or not isinstance(response_data.get("frames"), list):
        return False
    if not response_data["frames"]:
        return False
    for frame in response_data["frames"]:
        if frame.get("price_gross") is not None and frame.get("price_gross") != 0.0:
            return True
    return False
