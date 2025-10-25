# app/utils/sanitizer.py
"""
HTML sanitization utilities to prevent XSS attacks
Uses bleach library to clean potentially malicious HTML/JavaScript
"""

import bleach

# Allowed HTML tags (basic formatting only)
ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']

# No attributes allowed (prevents onclick, onerror, etc.)
ALLOWED_ATTRIBUTES = {}

def sanitize_html(text):
    """
    Remove potentially malicious HTML/JavaScript from text
    
    Args:
        text: String that may contain HTML/JavaScript
        
    Returns:
        Sanitized string with malicious code removed
        
    Example:
        >>> sanitize_html("<script>alert('XSS')</script>Hello")
        "Hello"
        >>> sanitize_html("<b>Bold</b> text")
        "<b>Bold</b> text"
    """
    if not text:
        return text
    
    if not isinstance(text, str):
        return text
    
    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True  # Strip disallowed tags instead of escaping
    )

def sanitize_dict(data, fields):
    """
    Sanitize specific fields in a dictionary
    
    Args:
        data: Dictionary containing user input
        fields: List of field names to sanitize
        
    Returns:
        Dictionary with sanitized fields
        
    Example:
        >>> data = {'name': 'Max', 'description': '<script>alert("XSS")</script>'}
        >>> sanitize_dict(data, ['description'])
        {'name': 'Max', 'description': ''}
    """
    if not data:
        return data
    
    for field in fields:
        if field in data and isinstance(data[field], str):
            data[field] = sanitize_html(data[field])
    
    return data

def sanitize_user_input(data):
    """
    Sanitize all text fields commonly used in user profiles
    
    Args:
        data: User registration/update data dictionary
        
    Returns:
        Dictionary with sanitized fields
    """
    text_fields = ['description', 'additional_info', 'bio', 'about']
    return sanitize_dict(data, text_fields)

def sanitize_dog_input(data):
    """
    Sanitize all text fields commonly used in dog profiles
    
    Args:
        data: Dog creation/update data dictionary
        
    Returns:
        Dictionary with sanitized fields
    """
    text_fields = ['description', 'health_notes', 'special_needs', 'personality']
    return sanitize_dict(data, text_fields)

def sanitize_event_input(data):
    """
    Sanitize all text fields commonly used in event data
    
    Args:
        data: Event creation/update data dictionary
        
    Returns:
        Dictionary with sanitized fields
    """
    text_fields = ['description', 'location_details', 'requirements']
    return sanitize_dict(data, text_fields)
