"""
Datetime Utilities

Provides timezone-aware datetime functions for consistent datetime handling
across the application. All datetimes are stored in UTC to avoid timezone issues.
"""

from datetime import datetime, timezone, timedelta


def utc_now():
    """
    Get current UTC datetime (timezone-aware).
    
    Returns:
        datetime: Current UTC datetime with timezone information
        
    Example:
        >>> now = utc_now()
        >>> print(now)
        2025-10-24 16:30:45.123456+00:00
    """
    return datetime.now(timezone.utc)


def utc_from_timestamp(timestamp):
    """
    Convert Unix timestamp to timezone-aware UTC datetime.
    
    Args:
        timestamp (float): Unix timestamp (seconds since epoch)
        
    Returns:
        datetime: UTC datetime with timezone information
        
    Example:
        >>> dt = utc_from_timestamp(1698163845)
        >>> print(dt)
        2023-10-24 16:30:45+00:00
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def format_datetime(dt, format_string='%Y-%m-%d %H:%M:%S'):
    """
    Format datetime to string in UTC.
    
    Args:
        dt (datetime): Datetime object to format
        format_string (str): strftime format string
        
    Returns:
        str: Formatted datetime string in UTC
        
    Example:
        >>> dt = utc_now()
        >>> formatted = format_datetime(dt, '%Y-%m-%d')
        >>> print(formatted)
        '2025-10-24'
    """
    if dt is None:
        return None
    
    # Convert to UTC if timezone-aware
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    
    return dt.strftime(format_string)


def parse_datetime(date_string, format_string='%Y-%m-%d %H:%M:%S'):
    """
    Parse datetime string to timezone-aware UTC datetime.
    
    Args:
        date_string (str): String representation of datetime
        format_string (str): strptime format string
        
    Returns:
        datetime: UTC datetime with timezone information
        
    Example:
        >>> dt = parse_datetime('2025-10-24 16:30:45')
        >>> print(dt)
        2025-10-24 16:30:45+00:00
    """
    if not date_string:
        return None
    
    # Parse as naive datetime, then make it timezone-aware in UTC
    naive_dt = datetime.strptime(date_string, format_string)
    return naive_dt.replace(tzinfo=timezone.utc)


def add_days(dt, days):
    """
    Add days to a datetime.
    
    Args:
        dt (datetime): Base datetime
        days (int): Number of days to add (can be negative)
        
    Returns:
        datetime: New datetime with days added
        
    Example:
        >>> now = utc_now()
        >>> tomorrow = add_days(now, 1)
        >>> yesterday = add_days(now, -1)
    """
    if dt is None:
        return None
    return dt + timedelta(days=days)


def add_hours(dt, hours):
    """
    Add hours to a datetime.
    
    Args:
        dt (datetime): Base datetime
        hours (int): Number of hours to add (can be negative)
        
    Returns:
        datetime: New datetime with hours added
        
    Example:
        >>> now = utc_now()
        >>> in_2_hours = add_hours(now, 2)
    """
    if dt is None:
        return None
    return dt + timedelta(hours=hours)


def is_expired(dt, hours=24):
    """
    Check if a datetime has expired (is older than specified hours).
    
    Args:
        dt (datetime): Datetime to check
        hours (int): Number of hours to consider as expiration time
        
    Returns:
        bool: True if expired, False otherwise
        
    Example:
        >>> created = utc_now()
        >>> # ... some time later
        >>> if is_expired(created, hours=24):
        ...     print("Token expired")
    """
    if dt is None:
        return True
    
    # Ensure comparison is with timezone-aware datetimes
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    expiration_time = add_hours(dt, hours)
    return utc_now() > expiration_time


def days_until(target_dt):
    """
    Calculate days until a target datetime.
    
    Args:
        target_dt (datetime): Target datetime
        
    Returns:
        int: Number of days until target (negative if in the past)
        
    Example:
        >>> event_date = add_days(utc_now(), 7)
        >>> days = days_until(event_date)
        >>> print(f"Event in {days} days")
        Event in 7 days
    """
    if target_dt is None:
        return None
    
    # Ensure comparison is with timezone-aware datetimes
    if target_dt.tzinfo is None:
        target_dt = target_dt.replace(tzinfo=timezone.utc)
    
    delta = target_dt - utc_now()
    return delta.days


def to_iso_format(dt):
    """
    Convert datetime to ISO 8601 format string.
    
    Args:
        dt (datetime): Datetime to convert
        
    Returns:
        str: ISO 8601 formatted string
        
    Example:
        >>> dt = utc_now()
        >>> iso = to_iso_format(dt)
        >>> print(iso)
        '2025-10-24T16:30:45.123456+00:00'
    """
    if dt is None:
        return None
    
    # Convert to UTC if timezone-aware
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    
    return dt.isoformat()


def from_iso_format(iso_string):
    """
    Parse ISO 8601 format string to datetime.
    
    Args:
        iso_string (str): ISO 8601 formatted string
        
    Returns:
        datetime: Timezone-aware datetime in UTC
        
    Example:
        >>> dt = from_iso_format('2025-10-24T16:30:45+00:00')
        >>> print(dt)
        2025-10-24 16:30:45+00:00
    """
    if not iso_string:
        return None
    
    dt = datetime.fromisoformat(iso_string)
    
    # Ensure it's timezone-aware and in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    
    return dt
