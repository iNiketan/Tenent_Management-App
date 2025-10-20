"""
Custom middleware for handling ngrok tunnels and CSRF
"""
from django.conf import settings


class NgrokCSRFMiddleware:
    """
    Middleware to dynamically add ngrok origins to CSRF_TRUSTED_ORIGINS
    This allows login and forms to work through ngrok tunnels
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get the origin from the request
        origin = request.META.get('HTTP_ORIGIN', '')
        host = request.get_host()
        
        # Check if this is an ngrok request
        if 'ngrok-free.app' in host or 'ngrok.io' in host:
            # Build the full origin URL
            if origin:
                trusted_origin = origin
            else:
                # Construct from host
                scheme = 'https' if request.is_secure() else 'http'
                trusted_origin = f'{scheme}://{host}'
            
            # Add to CSRF_TRUSTED_ORIGINS if not already there
            if hasattr(settings, 'CSRF_TRUSTED_ORIGINS'):
                if trusted_origin not in settings.CSRF_TRUSTED_ORIGINS:
                    settings.CSRF_TRUSTED_ORIGINS.append(trusted_origin)
            else:
                settings.CSRF_TRUSTED_ORIGINS = [trusted_origin]
        
        response = self.get_response(request)
        return response

