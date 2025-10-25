"""
Query Optimization Utilities

Provides helper functions and decorators for optimizing SQLAlchemy queries,
preventing N+1 query problems through eager loading strategies.
"""

from sqlalchemy.orm import joinedload, selectinload, subqueryload
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def with_relationships(*relationships):
    """
    Decorator to add eager loading to repository methods
    
    Usage:
        @with_relationships('owner', 'photos')
        def find_dogs_with_relations(self):
            return Dog.query.all()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            query = func(*args, **kwargs)
            if hasattr(query, 'options'):
                for rel in relationships:
                    query = query.options(joinedload(rel))
            return query
        return wrapper
    return decorator


def optimize_query_for_relationships(query, relationships):
    """
    Add eager loading options to a query
    
    Args:
        query: SQLAlchemy query object
        relationships: List of relationship names or tuples of nested relationships
        
    Returns:
        Query with eager loading options
        
    Example:
        query = Dog.query.filter_by(is_available=True)
        query = optimize_query_for_relationships(query, [
            'owner',
            ('photos', 'is_primary'),
            'matches.dog_two'
        ])
    """
    for rel in relationships:
        if isinstance(rel, tuple):
            # Nested relationships
            option = joinedload(rel[0])
            for nested in rel[1:]:
                option = option.joinedload(nested)
            query = query.options(option)
        elif isinstance(rel, str):
            # Simple relationship
            query = query.options(joinedload(rel))
    
    return query


class EagerLoadingStrategies:
    """
    Common eager loading patterns for different scenarios
    """
    
    @staticmethod
    def joined_load(*relationships):
        """
        Use JOIN to load relationships in same query
        Best for: one-to-one, small one-to-many
        """
        options = [joinedload(rel) for rel in relationships]
        return options
    
    @staticmethod
    def select_in_load(*relationships):
        """
        Use separate SELECT IN query for relationships
        Best for: large one-to-many, many-to-many
        """
        options = [selectinload(rel) for rel in relationships]
        return options
    
    @staticmethod
    def subquery_load(*relationships):
        """
        Use subquery to load relationships
        Best for: complex scenarios with filtering
        """
        options = [subqueryload(rel) for rel in relationships]
        return options
    
    @staticmethod
    def nested_load(primary_rel, *nested_rels):
        """
        Load nested relationships
        Example: owner -> dogs -> photos
        """
        option = joinedload(primary_rel)
        for nested in nested_rels:
            option = option.joinedload(nested)
        return [option]


def count_queries(func):
    """
    Decorator to log number of queries executed
    Useful for debugging N+1 issues
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        
        query_count = {'count': 0}
        
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            query_count['count'] += 1
        
        event.listen(Engine, "after_cursor_execute", receive_after_cursor_execute)
        
        result = func(*args, **kwargs)
        
        event.remove(Engine, "after_cursor_execute", receive_after_cursor_execute)
        
        logger.info(f"{func.__name__} executed {query_count['count']} queries")
        
        return result
    
    return wrapper


# Common relationship patterns for models

MATCH_RELATIONSHIPS = {
    'basic': ['dog_one', 'dog_two'],
    'with_owners': [
        ('dog_one', 'owner'),
        ('dog_two', 'owner')
    ],
    'with_photos': [
        ('dog_one', 'photos'),
        ('dog_two', 'photos')
    ],
    'full': [
        ('dog_one', 'owner'),
        ('dog_one', 'photos'),
        ('dog_two', 'owner'),
        ('dog_two', 'photos')
    ]
}

DOG_RELATIONSHIPS = {
    'basic': ['owner'],
    'with_photos': ['owner', 'photos'],
    'with_matches': ['owner', 'photos', 'matches_as_dog_one', 'matches_as_dog_two'],
    'full': ['owner', 'photos', 'matches_as_dog_one', 'matches_as_dog_two']
}

EVENT_RELATIONSHIPS = {
    'basic': ['organizer'],
    'with_registrations': ['organizer', 'registrations'],
    'full': [
        'organizer',
        ('registrations', 'user'),
        ('registrations', 'dog')
    ]
}

MESSAGE_RELATIONSHIPS = {
    'basic': ['match', 'sender'],
    'full': [
        'sender',
        ('match', 'dog_one'),
        ('match', 'dog_two')
    ]
}
