"""
Token-based impersonation system for separate tab sessions
"""
import secrets
import json
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class ImpersonationTokenManager:
    """Manages impersonation tokens for separate tab sessions"""
    
    TOKEN_PREFIX = "imp_token:"
    TOKEN_EXPIRY = timedelta(hours=8)  # 8 hour expiry for impersonation tokens
    
    @classmethod
    def create_token(cls, original_user_id, target_user_id, original_username, target_username):
        """Create a new impersonation token"""
        try:
            token = secrets.token_urlsafe(32)
            
            token_data = {
                'original_user_id': str(original_user_id),
                'target_user_id': str(target_user_id),
                'original_username': original_username,
                'target_username': target_username,
                'created_at': timezone.now().isoformat(),
                'expires_at': (timezone.now() + cls.TOKEN_EXPIRY).isoformat(),
            }
            
            # Store in cache with expiry
            cache_key = f"{cls.TOKEN_PREFIX}{token}"
            cache.set(cache_key, json.dumps(token_data), timeout=int(cls.TOKEN_EXPIRY.total_seconds()))
            
            logger.info(f"Created impersonation token for {original_username} -> {target_username}")
            return token
        except Exception as e:
            logger.error(f"Failed to create impersonation token: {e}")
            # Fallback: use a simple in-memory store (not ideal but prevents 500 error)
            return cls._create_fallback_token(original_user_id, target_user_id, original_username, target_username)
    
    @classmethod
    def get_token_data(cls, token):
        """Get impersonation data for a token"""
        if not token:
            return None
            
        try:
            cache_key = f"{cls.TOKEN_PREFIX}{token}"
            data = cache.get(cache_key)
            
            if not data:
                # Check fallback storage
                return cls._get_fallback_token_data(token)
                
            try:
                token_data = json.loads(data)
                
                # Check if token has expired
                expires_at = timezone.datetime.fromisoformat(token_data['expires_at'])
                if timezone.now() > expires_at:
                    cls.invalidate_token(token)
                    return None
                    
                return token_data
            except (json.JSONDecodeError, KeyError, ValueError):
                cls.invalidate_token(token)
                return None
        except Exception as e:
            logger.error(f"Failed to get token data: {e}")
            return cls._get_fallback_token_data(token)
    
    @classmethod
    def invalidate_token(cls, token):
        """Invalidate a token"""
        if not token:
            return
            
        cache_key = f"{cls.TOKEN_PREFIX}{token}"
        cache.delete(cache_key)
    
    @classmethod
    def extend_token(cls, token, additional_hours=2):
        """Extend a token's expiry time"""
        token_data = cls.get_token_data(token)
        if not token_data:
            return False
            
        # Update expiry time
        new_expiry = timezone.now() + timedelta(hours=additional_hours)
        token_data['expires_at'] = new_expiry.isoformat()
        
        # Update cache
        cache_key = f"{cls.TOKEN_PREFIX}{token}"
        timeout = int(timedelta(hours=additional_hours).total_seconds())
        cache.set(cache_key, json.dumps(token_data), timeout=timeout)
        
        return True
    
    @classmethod
    def get_user_tokens(cls, user_id):
        """Get all active tokens for a user (for cleanup purposes)"""
        # This is a simplified version - in production you might want to store
        # user-to-token mappings separately for better performance
        pass
    
    # Fallback storage for when cache is unavailable (Railway deployment issue)
    _fallback_tokens = {}
    
    @classmethod
    def _create_fallback_token(cls, original_user_id, target_user_id, original_username, target_username):
        """Create token using in-memory fallback storage"""
        token = secrets.token_urlsafe(32)
        
        token_data = {
            'original_user_id': str(original_user_id),
            'target_user_id': str(target_user_id),
            'original_username': original_username,
            'target_username': target_username,
            'created_at': timezone.now().isoformat(),
            'expires_at': (timezone.now() + cls.TOKEN_EXPIRY).isoformat(),
        }
        
        cls._fallback_tokens[token] = token_data
        logger.warning(f"Using fallback token storage for {original_username} -> {target_username}")
        return token
    
    @classmethod
    def _get_fallback_token_data(cls, token):
        """Get token data from fallback storage"""
        if not token or token not in cls._fallback_tokens:
            return None
            
        token_data = cls._fallback_tokens[token]
        
        try:
            # Check if token has expired
            expires_at = timezone.datetime.fromisoformat(token_data['expires_at'])
            if timezone.now() > expires_at:
                cls._fallback_tokens.pop(token, None)
                return None
                
            return token_data
        except (KeyError, ValueError):
            cls._fallback_tokens.pop(token, None)
            return None