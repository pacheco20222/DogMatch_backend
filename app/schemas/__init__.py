# app/schemas/__init__.py
"""
Marshmallow schemas package
Contains all validation schemas separated from models
"""

from .user_schemas import (
    UserRegistrationSchema,
    UserLoginSchema,
    Setup2FASchema,
    Verify2FASchema,
    UserUpdateSchema,
    UserResponseSchema
)

from .dog_schemas import (
    DogCreateSchema,
    DogUpdateSchema,
    DogResponseSchema,
    PhotoSchema
)

from .match_schemas import (
    SwipeActionSchema,
    MatchResponseSchema,
    MatchListSchema
)

from .message_schemas import (
    MessageCreateSchema,
    MessageUpdateSchema,
    MessageResponseSchema,
    MessageListSchema
)

from .event_schemas import (
    EventCreateSchema,
    EventUpdateSchema,
    EventResponseSchema,
    EventListSchema
)

from .event_registration_schemas import (
    EventRegistrationCreateSchema,
    EventRegistrationUpdateSchema,
    RegistrationApprovalSchema,
    PaymentProcessSchema,
    EventRegistrationResponseSchema,
    RegistrationListSchema
)

__all__ = [
    # User schemas
    'UserRegistrationSchema',
    'UserLoginSchema',
    'Setup2FASchema',
    'Verify2FASchema',
    'UserUpdateSchema',
    'UserResponseSchema',
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
    # Event Registration schemas
    'EventRegistrationCreateSchema',
    'EventRegistrationUpdateSchema',
    'RegistrationApprovalSchema',
    'PaymentProcessSchema',
    'EventRegistrationResponseSchema',
    'RegistrationListSchema',
]
