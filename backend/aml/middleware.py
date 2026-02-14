"""
Audit Trail Middleware
Logs all API requests and important actions for audit purposes
"""
import logging
import json
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

audit_logger = logging.getLogger('aml')


class AuditTrailMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests for audit trail
    """
    
    def process_request(self, request):
        """Log incoming request"""
        # Skip logging for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None
        
        # Log request details
        audit_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'user': request.user.username if hasattr(request.user, 'username') else 'anonymous',
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # Log request body for POST/PUT/PATCH (excluding sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = json.loads(request.body.decode('utf-8')) if request.body else {}
                # Remove sensitive fields
                sensitive_fields = ['password', 'secret', 'token', 'api_key']
                sanitized_body = {k: v for k, v in body.items() if k.lower() not in sensitive_fields}
                audit_data['request_body'] = sanitized_body
            except:
                pass
        
        audit_logger.info(f"API Request: {json.dumps(audit_data, ensure_ascii=False)}")
        
        return None
    
    def process_response(self, request, response):
        """Log response"""
        # Skip logging for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return response
        
        audit_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user': request.user.username if hasattr(request.user, 'username') else 'anonymous',
        }
        
        audit_logger.info(f"API Response: {json.dumps(audit_data, ensure_ascii=False)}")
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

