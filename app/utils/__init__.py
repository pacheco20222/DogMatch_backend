# app/utils/__init__.py
"""
Utility modules for DogMatch backend
"""

from .logger import setup_logger
from .sanitizer import (
    sanitize_html, 
    sanitize_dict, 
    sanitize_user_input, 
    sanitize_dog_input, 
    sanitize_event_input
)
from .datetime_utils import (
    utc_now,
    utc_from_timestamp,
    format_datetime,
    parse_datetime,
    add_days,
    add_hours,
    is_expired,
    days_until,
    to_iso_format,
    from_iso_format
)
from .cache import (
    cache,
    make_user_cache_key,
    make_dog_cache_key,
    make_dog_list_cache_key,
    make_match_cache_key,
    make_event_cache_key,
    make_event_list_cache_key,
    make_message_cache_key,
    make_available_dogs_cache_key,
    invalidate_user_cache,
    invalidate_dog_cache,
    invalidate_match_cache,
    invalidate_event_cache,
    invalidate_event_list_cache,
    invalidate_message_cache,
    invalidate_available_dogs_cache,
    cached_response,
    cache_result,
    get_cache_stats,
    clear_all_cache,
    get_or_set_cache
)

__all__ = [
    'setup_logger',
    'sanitize_html',
    'sanitize_dict',
    'sanitize_user_input',
    'sanitize_dog_input',
    'sanitize_event_input',
    'utc_now',
    'utc_from_timestamp',
    'format_datetime',
    'parse_datetime',
    'add_days',
    'add_hours',
    'is_expired',
    'days_until',
    'to_iso_format',
    'from_iso_format',
    'cache',
    'make_user_cache_key',
    'make_dog_cache_key',
    'make_dog_list_cache_key',
    'make_match_cache_key',
    'make_event_cache_key',
    'make_event_list_cache_key',
    'make_message_cache_key',
    'make_available_dogs_cache_key',
    'invalidate_user_cache',
    'invalidate_dog_cache',
    'invalidate_match_cache',
    'invalidate_event_cache',
    'invalidate_event_list_cache',
    'invalidate_message_cache',
    'invalidate_available_dogs_cache',
    'cached_response',
    'cache_result',
    'get_cache_stats',
    'clear_all_cache',
    'get_or_set_cache'
]
