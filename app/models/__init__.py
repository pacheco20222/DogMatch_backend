# app/models/__init__.py
"""
Models package initialization
Centralizes all model imports for clean importing throughout the application
"""

# User models and schemas
from .user import (
    User,
    BlacklistedToken,
    UserRegistrationSchema,
    UserLoginSchema,
    UserUpdateSchema,
    UserResponseSchema,
    Setup2FASchema,
    Verify2FASchema
)

# Dog models and schemas
from .dog import (
    Dog,
    Photo,
    DogCreateSchema,
    DogUpdateSchema,
    DogResponseSchema,
    PhotoSchema
)

# Match models and schemas
from .match import (
    Match,
    SwipeActionSchema,
    MatchResponseSchema,
    MatchListSchema
)

# Message models and schemas
from .message import (
    Message,
    MessageCreateSchema,
    MessageUpdateSchema,
    MessageResponseSchema,
    MessageListSchema
)

# Event models and schemas
from .event import (
    Event,
    EventCreateSchema,
    EventUpdateSchema,
    EventResponseSchema,
    EventListSchema
)

# EventRegistration models and schemas
from .event_registration import (
    EventRegistration,
    EventRegistrationCreateSchema,
    EventRegistrationUpdateSchema,
    RegistrationApprovalSchema,
    PaymentProcessSchema,
    EventRegistrationResponseSchema,
    RegistrationListSchema
)

# Make all models and schemas available at package level
__all__ = [
    # User models
    'User',
    'BlacklistedToken',
    
    # Dog models
    'Dog',
    'Photo',
    
    # Match models
    'Match',
    
    # Message models
    'Message',
    
    # Event models
    'Event',
    
    # EventRegistration models
    'EventRegistration',
    
    # User schemas
    'UserRegistrationSchema',
    'UserLoginSchema',
    'UserUpdateSchema',
    'UserResponseSchema',
    'Setup2FASchema',
    'Verify2FASchema',
    
    # Dog schemas
    'DogCreateSchema',
    'DogUpdateSchema',
    'DogResponseSchema',
    'PhotoSchema',
    
    # Match schemas
    'SwipeActionSchema',
    'MatchResponseSchema',
    'MatchListSchema',
    
    # Message schemas
    'MessageCreateSchema',
    'MessageUpdateSchema',
    'MessageResponseSchema',
    'MessageListSchema',
    
    # Event schemas
    'EventCreateSchema',
    'EventUpdateSchema',
    'EventResponseSchema',
    'EventListSchema',
    
    # EventRegistration schemas
    'EventRegistrationCreateSchema',
    'EventRegistrationUpdateSchema',
    'RegistrationApprovalSchema',
    'PaymentProcessSchema',
    'EventRegistrationResponseSchema',
    'RegistrationListSchema',
]