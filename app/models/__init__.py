# app/models/__init__.py
"""
Models package initialization
Centralizes all model imports for clean importing throughout the application
"""

# User models only (schemas are in app.schemas.user_schemas)
from .user import User, BlacklistedToken

# Dog models only (schemas are in app.schemas.dog_schemas)
from .dog import Dog, Photo

# Match models only (schemas are in app.schemas.match_schemas)
from .match import Match

# Message models only (schemas are in app.schemas.message_schemas)
from .message import Message

# Event models only (schemas are in app.schemas.event_schemas)
from .event import Event

# EventRegistration models only (schemas are in app.schemas.event_registration_schemas)
from .event_registration import EventRegistration

# Make all models available at package level
__all__ = [
    'User',
    'BlacklistedToken',
    'Dog',
    'Photo',
    'Match',
    'Message',
    'Event',
    'EventRegistration',
]