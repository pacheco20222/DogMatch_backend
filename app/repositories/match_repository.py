"""
Match Repository

Handles all database operations for Match model.
Provides methods for querying, creating, updating, and deleting matches.
Includes optimized methods with eager loading to prevent N+1 queries.
"""

from app import db
from app.models.match import Match
from app.models.dog import Dog
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timezone


class MatchRepository:
    """Repository for Match model data access"""
    
    @staticmethod
    def find_by_id(match_id):
        """
        Find match by ID
        
        Args:
            match_id: Match ID
            
        Returns:
            Match or None
        """
        return Match.query.get(match_id)
    
    @staticmethod
    def find_between_dogs(dog_one_id, dog_two_id):
        """
        Find match between two dogs (in either direction)
        
        Args:
            dog_one_id: First dog ID
            dog_two_id: Second dog ID
            
        Returns:
            Match or None
        """
        return Match.query.filter(
            or_(
                and_(Match.dog_one_id == dog_one_id, Match.dog_two_id == dog_two_id),
                and_(Match.dog_one_id == dog_two_id, Match.dog_two_id == dog_one_id)
            )
        ).first()
    
    @staticmethod
    def find_by_dog(dog_id, status=None):
        """
        Find all matches for a dog
        
        Args:
            dog_id: Dog ID
            status: Optional status filter
            
        Returns:
            list: List of matches
        """
        query = Match.query.filter(
            or_(Match.dog_one_id == dog_id, Match.dog_two_id == dog_id)
        )
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Match.created_at.desc()).all()
    
    @staticmethod
    def find_by_dogs(dog_ids, status=None):
        """
        Find all matches for multiple dogs
        
        Args:
            dog_ids: List of dog IDs
            status: Optional status filter
            
        Returns:
            list: List of matches
        """
        query = Match.query.filter(
            or_(
                Match.dog_one_id.in_(dog_ids),
                Match.dog_two_id.in_(dog_ids)
            )
        )
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Match.matched_at.desc()).all()
    
    @staticmethod
    def create(match_data):
        """
        Create a new match
        
        Args:
            match_data: Dictionary of match attributes
            
        Returns:
            Match: Created match object
        """
        match = Match(**match_data)
        db.session.add(match)
        db.session.commit()
        db.session.refresh(match)
        return match
    
    @staticmethod
    def update(match, updates):
        """
        Update match attributes
        
        Args:
            match: Match object to update
            updates: Dictionary of fields to update
            
        Returns:
            Match: Updated match object
        """
        for key, value in updates.items():
            if hasattr(match, key):
                setattr(match, key, value)
        
        match.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        db.session.refresh(match)
        return match
    
    @staticmethod
    def delete(match):
        """
        Delete a match
        
        Args:
            match: Match object to delete
            
        Returns:
            bool: True if successful
        """
        db.session.delete(match)
        db.session.commit()
        return True
    
    @staticmethod
    def find_matched(dog_ids):
        """
        Find all matched pairs for given dogs
        
        Args:
            dog_ids: List of dog IDs
            
        Returns:
            list: List of matched matches
        """
        return Match.query.filter(
            and_(
                or_(
                    Match.dog_one_id.in_(dog_ids),
                    Match.dog_two_id.in_(dog_ids)
                ),
                Match.status == 'matched'
            )
        ).order_by(Match.matched_at.desc()).all()
    
    @staticmethod
    def find_pending_likes(dog_id):
        """
        Find dogs that have liked the given dog (pending swipes)
        
        Args:
            dog_id: Dog ID
            
        Returns:
            list: List of matches where dog is dog_two and dog_one liked
        """
        return Match.query.filter(
            and_(
                Match.dog_two_id == dog_id,
                Match.dog_one_liked == True,
                Match.status == 'pending'
            )
        ).all()
    
    @staticmethod
    def find_swiped_dog_ids(dog_id):
        """
        Get IDs of all dogs this dog has swiped on
        
        Args:
            dog_id: Dog ID
            
        Returns:
            set: Set of dog IDs
        """
        matches = Match.query.filter(
            or_(Match.dog_one_id == dog_id, Match.dog_two_id == dog_id)
        ).all()
        
        swiped_ids = set()
        for match in matches:
            if match.dog_one_id == dog_id:
                swiped_ids.add(match.dog_two_id)
            else:
                swiped_ids.add(match.dog_one_id)
        
        return swiped_ids
    
    @staticmethod
    def count_by_dog(dog_id, status=None):
        """
        Count matches for a dog
        
        Args:
            dog_id: Dog ID
            status: Optional status filter
            
        Returns:
            int: Number of matches
        """
        query = Match.query.filter(
            or_(Match.dog_one_id == dog_id, Match.dog_two_id == dog_id)
        )
        
        if status:
            query = query.filter_by(status=status)
        
        return query.count()
    
    @staticmethod
    def count_matches_for_dogs(dog_ids):
        """
        Count total matches for multiple dogs
        
        Args:
            dog_ids: List of dog IDs
            
        Returns:
            int: Total match count
        """
        return Match.query.filter(
            and_(
                or_(
                    Match.dog_one_id.in_(dog_ids),
                    Match.dog_two_id.in_(dog_ids)
                ),
                Match.status == 'matched'
            )
        ).count()
    
    @staticmethod
    def count_pending_likes_for_dogs(dog_ids):
        """
        Count pending likes for multiple dogs
        
        Args:
            dog_ids: List of dog IDs
            
        Returns:
            int: Total pending likes
        """
        return Match.query.filter(
            and_(
                Match.dog_two_id.in_(dog_ids),
                Match.dog_one_liked == True,
                Match.status == 'pending'
            )
        ).count()
    
    @staticmethod
    def count_swipes_by_dogs(dog_ids):
        """
        Count total swipes made by dogs
        
        Args:
            dog_ids: List of dog IDs
            
        Returns:
            int: Total swipe count
        """
        return Match.query.filter(Match.dog_one_id.in_(dog_ids)).count()
    
    @staticmethod
    def find_by_status(status, limit=100, offset=0):
        """
        Find all matches with a specific status
        
        Args:
            status: Match status
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            list: List of matches
        """
        return Match.query.filter_by(status=status).order_by(
            Match.created_at.desc()
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def exists_between_dogs(dog_one_id, dog_two_id):
        """
        Check if match exists between two dogs
        
        Args:
            dog_one_id: First dog ID
            dog_two_id: Second dog ID
            
        Returns:
            bool: True if match exists
        """
        return db.session.query(
            Match.query.filter(
                or_(
                    and_(Match.dog_one_id == dog_one_id, Match.dog_two_id == dog_two_id),
                    and_(Match.dog_one_id == dog_two_id, Match.dog_two_id == dog_one_id)
                )
            ).exists()
        ).scalar()
    
    # ==================== OPTIMIZED METHODS (Prevent N+1 Queries) ====================
    
    @staticmethod
    def find_by_id_with_dogs(match_id):
        """
        Find match by ID with dogs eager loaded (prevents N+1)
        
        Args:
            match_id: Match ID
            
        Returns:
            Match or None with dog_one and dog_two loaded
        """
        return Match.query.options(
            joinedload(Match.dog_one),
            joinedload(Match.dog_two)
        ).get(match_id)
    
    @staticmethod
    def find_by_id_with_dogs_and_owners(match_id):
        """
        Find match by ID with dogs and owners eager loaded (prevents N+1)
        
        Args:
            match_id: Match ID
            
        Returns:
            Match or None with dog_one, dog_two, and their owners loaded
        """
        return Match.query.options(
            joinedload(Match.dog_one).joinedload(Dog.owner),
            joinedload(Match.dog_two).joinedload(Dog.owner)
        ).get(match_id)
    
    @staticmethod
    def find_by_dog_with_relations(dog_id, status=None):
        """
        Find all matches for a dog with related dogs and owners eager loaded
        Optimized to prevent N+1 queries
        
        Args:
            dog_id: Dog ID
            status: Optional status filter
            
        Returns:
            list: List of matches with relationships loaded
        """
        query = Match.query.filter(
            or_(Match.dog_one_id == dog_id, Match.dog_two_id == dog_id)
        ).options(
            joinedload(Match.dog_one).joinedload(Dog.owner),
            joinedload(Match.dog_two).joinedload(Dog.owner),
            selectinload(Match.dog_one).selectinload(Dog.photos),
            selectinload(Match.dog_two).selectinload(Dog.photos)
        )
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Match.created_at.desc()).all()
    
    @staticmethod
    def find_by_dogs_with_relations(dog_ids, status=None):
        """
        Find all matches for multiple dogs with relationships eager loaded
        Optimized to prevent N+1 queries
        
        Args:
            dog_ids: List of dog IDs
            status: Optional status filter
            
        Returns:
            list: List of matches with relationships loaded
        """
        query = Match.query.filter(
            or_(
                Match.dog_one_id.in_(dog_ids),
                Match.dog_two_id.in_(dog_ids)
            )
        ).options(
            joinedload(Match.dog_one).joinedload(Dog.owner),
            joinedload(Match.dog_two).joinedload(Dog.owner),
            selectinload(Match.dog_one).selectinload(Dog.photos),
            selectinload(Match.dog_two).selectinload(Dog.photos)
        )
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Match.matched_at.desc()).all()
    
    @staticmethod
    def find_matched_with_full_details(dog_ids):
        """
        Find all matched pairs with full details (dogs, owners, photos)
        Highly optimized for display purposes
        
        Args:
            dog_ids: List of dog IDs
            
        Returns:
            list: List of fully loaded matches
        """
        return Match.query.filter(
            and_(
                or_(
                    Match.dog_one_id.in_(dog_ids),
                    Match.dog_two_id.in_(dog_ids)
                ),
                Match.status == 'matched'
            )
        ).options(
            joinedload(Match.dog_one).joinedload(Dog.owner),
            joinedload(Match.dog_two).joinedload(Dog.owner),
            selectinload(Match.dog_one).selectinload(Dog.photos),
            selectinload(Match.dog_two).selectinload(Dog.photos)
        ).order_by(Match.matched_at.desc()).all()
    
    @staticmethod
    def find_pending_likes_with_dogs(dog_id):
        """
        Find dogs that have liked the given dog with full dog details
        Optimized for "who liked me" screen
        
        Args:
            dog_id: Dog ID
            
        Returns:
            list: List of matches with dog_one fully loaded
        """
        return Match.query.filter(
            and_(
                Match.dog_two_id == dog_id,
                Match.dog_one_liked == True,
                Match.status == 'pending'
            )
        ).options(
            joinedload(Match.dog_one).joinedload(Dog.owner),
            selectinload(Match.dog_one).selectinload(Dog.photos)
        ).all()

