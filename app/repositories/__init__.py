"""
Repositories Package

Provides data access layer for all models, abstracting database queries
and operations. Repositories handle CRUD operations and complex queries.
"""

from .user_repository import UserRepository
from .dog_repository import DogRepository
from .match_repository import MatchRepository
from .event_repository import EventRepository
from .message_repository import MessageRepository

__all__ = [
    'UserRepository',
    'DogRepository',
    'MatchRepository',
    'EventRepository',
    'MessageRepository'
]
