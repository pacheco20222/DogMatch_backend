"""
Match Service Layer

Handles all business logic related to dog matching including:
- Swipe functionality (like/pass)
- Match creation when mutual likes occur
- Match status management
- Match queries
"""

from app import db
from app.models.match import Match
from app.models.dog import Dog
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class MatchService:
    """Service class for match-related business logic"""
    
    @staticmethod
    def swipe(user_id, dog_id, target_dog_id, action):
        """
        Process a swipe action (like or pass)
        
        Args:
            user_id: ID of the user performing the swipe
            dog_id: ID of the user's dog
            target_dog_id: ID of the dog being swiped on
            action: 'like' or 'pass'
            
        Returns:
            dict: Contains match info and whether it's a new match
            
        Raises:
            ValueError: If validation fails
        """
        # Validate dogs exist
        dog = Dog.query.get(dog_id)
        target_dog = Dog.query.get(target_dog_id)
        
        if not dog or not target_dog:
            raise ValueError("Dog not found")
        
        # Verify ownership
        if dog.owner_id != user_id:
            raise PermissionError("You don't own this dog")
        
        # Can't swipe on own dogs
        if dog.owner_id == target_dog.owner_id:
            raise ValueError("Cannot swipe on your own dog")
        
        # Check if already swiped
        existing_match = Match.query.filter(
            ((Match.dog_one_id == dog_id) & (Match.dog_two_id == target_dog_id)) |
            ((Match.dog_one_id == target_dog_id) & (Match.dog_two_id == dog_id))
        ).first()
        
        if existing_match:
            raise ValueError("Already swiped on this dog")
        
        # Create match record
        match = Match(
            dog_one_id=dog_id,
            dog_two_id=target_dog_id,
            status='pending'  # Will be updated if mutual like
        )
        
        if action == 'like':
            match.dog_one_liked = True
            
            # Check if target dog already liked back
            reverse_match = Match.query.filter_by(
                dog_one_id=target_dog_id,
                dog_two_id=dog_id,
                dog_one_liked=True
            ).first()
            
            if reverse_match:
                # It's a mutual match!
                match.status = 'matched'
                match.dog_two_liked = True
                match.matched_at = datetime.now(timezone.utc)
                
                # Update reverse match as well
                reverse_match.status = 'matched'
                reverse_match.dog_two_liked = True
                reverse_match.matched_at = datetime.now(timezone.utc)
                
                db.session.add(match)
                db.session.commit()
                
                logger.info(f"New match created: Dog {dog_id} <-> Dog {target_dog_id}")
                
                return {
                    'match': match,
                    'is_new_match': True,
                    'message': "It's a match! 🎉"
                }
        else:  # action == 'pass'
            match.dog_one_liked = False
        
        db.session.add(match)
        db.session.commit()
        
        logger.info(f"Swipe recorded: Dog {dog_id} {action}d Dog {target_dog_id}")
        
        return {
            'match': match,
            'is_new_match': False,
            'message': f"Swipe {action} recorded"
        }
    
    @staticmethod
    def get_matches_for_dog(dog_id, owner_id, status=None):
        """
        Get all matches for a dog
        
        Args:
            dog_id: Dog ID
            owner_id: Owner ID (for authorization)
            status: Optional filter by status ('pending', 'matched', etc.)
            
        Returns:
            list: List of matches
            
        Raises:
            PermissionError: If user doesn't own the dog
        """
        # Verify ownership
        dog = Dog.query.get(dog_id)
        if not dog or dog.owner_id != owner_id:
            raise PermissionError("You don't own this dog")
        
        # Build query
        query = Match.query.filter(
            ((Match.dog_one_id == dog_id) | (Match.dog_two_id == dog_id))
        )
        
        # Filter by status if provided
        if status:
            query = query.filter_by(status=status)
        
        matches = query.order_by(Match.created_at.desc()).all()
        
        return matches
    
    @staticmethod
    def get_matches_for_user(user_id, status='matched'):
        """
        Get all matches for all of a user's dogs
        
        Args:
            user_id: User ID
            status: Filter by status (default: 'matched')
            
        Returns:
            list: List of matches
        """
        # Get all user's dogs
        user_dogs = Dog.query.filter_by(owner_id=user_id).all()
        dog_ids = [dog.id for dog in user_dogs]
        
        if not dog_ids:
            return []
        
        # Get matches for these dogs
        matches = Match.query.filter(
            ((Match.dog_one_id.in_(dog_ids)) | (Match.dog_two_id.in_(dog_ids))) &
            (Match.status == status)
        ).order_by(Match.matched_at.desc()).all()
        
        return matches
    
    @staticmethod
    def unmatch(match_id, user_id):
        """
        Unmatch two dogs
        
        Args:
            match_id: Match ID
            user_id: User ID (for authorization)
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If match not found
            PermissionError: If user doesn't own either dog
        """
        match = Match.query.get(match_id)
        if not match:
            raise ValueError("Match not found")
        
        # Verify user owns one of the dogs
        dog_one = Dog.query.get(match.dog_one_id)
        dog_two = Dog.query.get(match.dog_two_id)
        
        if dog_one.owner_id != user_id and dog_two.owner_id != user_id:
            raise PermissionError("You are not part of this match")
        
        # Update match status
        match.status = 'unmatched'
        match.unmatched_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"Match unmatched: {match_id} by user {user_id}")
        return True
    
    @staticmethod
    def get_match_by_id(match_id):
        """Get match by ID"""
        return Match.query.get(match_id)
    
    @staticmethod
    def get_pending_swipes_for_dog(dog_id, owner_id):
        """
        Get dogs that have liked this dog but haven't been swiped on yet
        
        Args:
            dog_id: Dog ID
            owner_id: Owner ID (for authorization)
            
        Returns:
            list: List of dogs that have liked this dog
        """
        # Verify ownership
        dog = Dog.query.get(dog_id)
        if not dog or dog.owner_id != owner_id:
            raise PermissionError("You don't own this dog")
        
        # Find matches where this dog is dog_two and dog_one liked
        pending_matches = Match.query.filter(
            (Match.dog_two_id == dog_id) &
            (Match.dog_one_liked == True) &
            (Match.status == 'pending')
        ).all()
        
        # Get the dogs that liked
        dog_ids = [match.dog_one_id for match in pending_matches]
        dogs = Dog.query.filter(Dog.id.in_(dog_ids)).all() if dog_ids else []
        
        return dogs
    
    @staticmethod
    def get_swipe_candidates(dog_id, owner_id, limit=20):
        """
        Get dogs that haven't been swiped on yet
        
        Args:
            dog_id: Dog ID
            owner_id: Owner ID (for authorization)
            limit: Maximum number of candidates to return
            
        Returns:
            list: List of dogs to swipe on
        """
        # Verify ownership
        dog = Dog.query.get(dog_id)
        if not dog or dog.owner_id != owner_id:
            raise PermissionError("You don't own this dog")
        
        # Get IDs of dogs already swiped on
        swiped_matches = Match.query.filter(
            ((Match.dog_one_id == dog_id) | (Match.dog_two_id == dog_id))
        ).all()
        
        swiped_dog_ids = set()
        for match in swiped_matches:
            if match.dog_one_id == dog_id:
                swiped_dog_ids.add(match.dog_two_id)
            else:
                swiped_dog_ids.add(match.dog_one_id)
        
        # Get available dogs not yet swiped on (excluding own dogs)
        query = Dog.query.filter(
            (Dog.is_available == True) &
            (Dog.owner_id != owner_id) &
            (~Dog.id.in_(swiped_dog_ids))
        ).order_by(Dog.created_at.desc()).limit(limit)
        
        candidates = query.all()
        
        return candidates
    
    @staticmethod
    def get_match_statistics(user_id):
        """
        Get match statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            dict: Statistics including total matches, pending likes, etc.
        """
        # Get user's dogs
        user_dogs = Dog.query.filter_by(owner_id=user_id).all()
        dog_ids = [dog.id for dog in user_dogs]
        
        if not dog_ids:
            return {
                'total_matches': 0,
                'pending_likes': 0,
                'total_swipes': 0
            }
        
        # Count matches
        total_matches = Match.query.filter(
            ((Match.dog_one_id.in_(dog_ids)) | (Match.dog_two_id.in_(dog_ids))) &
            (Match.status == 'matched')
        ).count()
        
        # Count pending likes (dogs that liked user's dogs)
        pending_likes = Match.query.filter(
            (Match.dog_two_id.in_(dog_ids)) &
            (Match.dog_one_liked == True) &
            (Match.status == 'pending')
        ).count()
        
        # Count total swipes made
        total_swipes = Match.query.filter(
            Match.dog_one_id.in_(dog_ids)
        ).count()
        
        return {
            'total_matches': total_matches,
            'pending_likes': pending_likes,
            'total_swipes': total_swipes
        }
