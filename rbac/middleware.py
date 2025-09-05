"""
Middleware for handling impersonation tokens
"""
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from .impersonation_tokens import ImpersonationTokenManager

User = get_user_model()

class ImpersonationTokenMiddleware:
    """Middleware to handle impersonation via URL tokens"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check for impersonation token in URL or POST data
        impersonation_token = request.GET.get('imp_token') or request.POST.get('imp_token')
        
        if impersonation_token:
            self.handle_impersonation_token(request, impersonation_token)
        
        response = self.get_response(request)
        return response
    
    def handle_impersonation_token(self, request, token):
        """Handle impersonation token with robust error handling"""
        try:
            token_data = ImpersonationTokenManager.get_token_data(token)
            
            if not token_data:
                # Don't show error message as token might be expired - just silently ignore
                return
            
            # Get the target user to impersonate
            target_user = User.objects.get(id=token_data['target_user_id'])
            original_user = User.objects.get(id=token_data['original_user_id'])
            
            # Store impersonation info in request for this session
            request.impersonation_data = {
                'is_impersonating': True,
                'original_user': original_user,
                'target_user': target_user,
                'token': token,
                'original_username': token_data['original_username'],
                'target_username': token_data['target_username'],
                'created_at': token_data['created_at']
            }
            
            # Override the user for this request
            request.user = target_user
            
        except User.DoesNotExist:
            # User not found - token is invalid, silently ignore
            return
        except (KeyError, TypeError, ValueError) as e:
            # Invalid token data - silently ignore to prevent 500 errors
            return
        except Exception as e:
            # Any other error - log it but don't break the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Impersonation middleware error: {e}")
            return