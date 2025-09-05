"""
Template tags for RBAC and impersonation functionality
"""
from django import template
from django.http import QueryDict
from ..impersonation import is_impersonating, get_impersonation_info

register = template.Library()

@register.filter
def is_impersonating(request):
    """Check if the current request is impersonating"""
    from ..impersonation import is_impersonating as _is_impersonating
    return _is_impersonating(request)

@register.filter  
def impersonation_info(request):
    """Get impersonation info for current request"""
    from ..impersonation import get_impersonation_info
    return get_impersonation_info(request)

@register.simple_tag
def impersonation_token(request):
    """Get the current impersonation token"""
    return request.GET.get('imp_token', '')

@register.simple_tag
def add_imp_token(url, request):
    """Add impersonation token to URL if present"""
    token = request.GET.get('imp_token')
    if not token:
        return url
    
    separator = '&' if '?' in url else '?'
    return f"{url}{separator}imp_token={token}"

@register.inclusion_tag('rbac/impersonation_url_params.html')
def preserve_impersonation_params(request):
    """Include hidden inputs to preserve impersonation parameters in forms"""
    token = request.GET.get('imp_token')
    return {'imp_token': token}