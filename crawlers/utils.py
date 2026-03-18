import re
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Vietnam UTC offset
_VN_UTC_OFFSET = 7

# Common absolute date/time formats encountered on Vietnamese news sites
_ABSOLUTE_FORMATS = [
    '%d/%m/%Y %H:%M',           # 25/12/2023 14:30
    '%d/%m/%Y, %H:%M',          # 25/12/2023, 14:30
    '%d/%m/%Y - %H:%M',         # 25/12/2023 - 14:30
    '%d-%m-%Y %H:%M',           # 25-12-2023 14:30
    '%d/%m/%Y',                  # 25/12/2023
    '%Y-%m-%dT%H:%M:%S',        # ISO 2023-12-25T14:30:00
    '%Y-%m-%dT%H:%M:%S%z',      # ISO with tz
    '%Y-%m-%d %H:%M:%S',        # 2023-12-25 14:30:00
    '%Y-%m-%d %H:%M',           # 2023-12-25 14:30
    '%Y-%m-%d',                  # 2023-12-25
]

# "Thứ X, dd/mm/yyyy, HH:MM" – strip the day-of-week prefix first
_DOW_PREFIX = re.compile(
    r'^(thứ\s+\w+,?\s*|chủ\s+nhật,?\s*)',
    re.IGNORECASE | re.UNICODE,
)

# Timezone suffixes like "(GMT+7)", "GMT+7", "(UTC+7)", "(UTC+07:00)" at end of string
_TZ_SUFFIX = re.compile(
    r'\s*\(?\s*(?:GMT|UTC)\s*[+-]\s*\d{1,2}(?::\d{2})?\s*\)?\s*$',
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Chuẩn hóa text: bỏ khoảng trắng thừa."""
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_time(time_str: str) -> str | None:
    """
    Parse a Vietnamese news date/time string and return an ISO-formatted
    string ``"YYYY-MM-DD HH:MM:SS"`` (Vietnam local time), or ``None`` if the
    string cannot be interpreted.

    Supported formats
    -----------------
    * Relative: "N giờ trước", "N phút trước", "N ngày trước", "hôm qua"
    * Absolute: dd/mm/yyyy HH:MM[, …], ISO variants, prefixed by day-of-week
    * Timezone suffixes like "(GMT+7)" are stripped before parsing.
    * Does **not** fall back to ``datetime.now()`` – returns ``None`` instead.

    Examples (format check – dates are fixed, not relative)::

        >>> parse_time("Thứ tư, 18/3/2026, 09:41 (GMT+7)")
        '2026-03-18 09:41:00'
        >>> parse_time("Thứ ba, 17/3/2026, 21:18 (GMT+7)")
        '2026-03-17 21:18:00'
        >>> parse_time("garbage string xyz")  # cannot parse
        >>> parse_time("")                     # empty input
    """
    if not time_str:
        return None

    raw = time_str.strip()
    lower = raw.lower()

    # --- 1. Relative expressions ---
    now = datetime.utcnow() + timedelta(hours=_VN_UTC_OFFSET)

    if 'giờ trước' in lower or 'tiếng trước' in lower:
        m = re.search(r'(\d+)', lower)
        if m:
            dt = now - timedelta(hours=int(m.group(1)))
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'phút trước' in lower:
        m = re.search(r'(\d+)', lower)
        if m:
            dt = now - timedelta(minutes=int(m.group(1)))
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'ngày trước' in lower:
        m = re.search(r'(\d+)', lower)
        if m:
            dt = now - timedelta(days=int(m.group(1)))
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'hôm qua' in lower:
        dt = now - timedelta(days=1)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'hôm nay' in lower:
        # Extract HH:MM if present, otherwise use start of day
        m = re.search(r'(\d{1,2}):(\d{2})', lower)
        if m:
            dt = now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0)
        else:
            dt = now.replace(hour=0, minute=0, second=0)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    # --- 2. Absolute expressions ---
    # Strip Vietnamese day-of-week prefix, e.g. "Thứ Hai, 25/12/2023, 14:30"
    cleaned = _DOW_PREFIX.sub('', raw).strip().lstrip(',').strip()
    # Strip trailing timezone suffix, e.g. "(GMT+7)", "GMT+7", "(UTC+7)"
    cleaned = _TZ_SUFFIX.sub('', cleaned).strip().rstrip(',').strip()

    for fmt in _ABSOLUTE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            # If the format has timezone info, convert to VN local time
            if dt.tzinfo is not None:
                import calendar
                utc_ts = calendar.timegm(dt.utctimetuple())
                dt = datetime.utcfromtimestamp(utc_ts) + timedelta(hours=_VN_UTC_OFFSET)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue

    logger.warning("parse_time: cannot parse %r – returning None", time_str)
    return None