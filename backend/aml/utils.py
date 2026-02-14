"""
Utility functions for AML system
"""
import json
import logging
from functools import wraps
from django.utils import timezone

audit_logger = logging.getLogger('aml')


def audit_log(action_name):
    """
    Decorator to log important actions for audit trail
    
    Usage:
        @audit_log('create_customer')
        def create_customer(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            audit_data = {
                'timestamp': timezone.now().isoformat(),
                'action': action_name,
                'function': f"{func.__module__}.{func.__name__}",
            }
            
            try:
                result = func(*args, **kwargs)
                audit_data['status'] = 'success'
                
                # Log result if it's a model instance
                if hasattr(result, 'pk'):
                    audit_data['object_id'] = str(result.pk)
                    if hasattr(result, '__class__'):
                        audit_data['object_type'] = result.__class__.__name__
                
                audit_logger.info(f"Action: {json.dumps(audit_data, ensure_ascii=False)}")
                return result
                
            except Exception as e:
                audit_data['status'] = 'error'
                audit_data['error'] = str(e)
                audit_logger.error(f"Action Error: {json.dumps(audit_data, ensure_ascii=False)}")
                raise
        
        return wrapper
    return decorator


def log_alert_generation(alert, transaction, triggered_rules):
    """Log alert generation for audit"""
    audit_data = {
        'timestamp': timezone.now().isoformat(),
        'action': 'alert_generated',
        'alert_id': alert.alert_id,
        'transaction_id': transaction.transaction_id,
        'customer_id': transaction.customer.customer_id,
        'severity': alert.severity,
        'risk_score': str(alert.risk_score),
        'triggered_rules': [rule.name for rule in triggered_rules],
    }
    audit_logger.info(f"Alert Generated: {json.dumps(audit_data, ensure_ascii=False)}")


def log_report_generation(report, report_type):
    """Log report generation for audit"""
    audit_data = {
        'timestamp': timezone.now().isoformat(),
        'action': 'report_generated',
        'report_id': report.report_id,
        'report_type': report_type,
        'status': report.status,
        'submitted_by': report.submitted_by,
    }
    audit_logger.info(f"Report Generated: {json.dumps(audit_data, ensure_ascii=False)}")


def log_alert_review(alert, reviewer, status, notes):
    """Log alert review for audit"""
    audit_data = {
        'timestamp': timezone.now().isoformat(),
        'action': 'alert_reviewed',
        'alert_id': alert.alert_id,
        'reviewer': reviewer,
        'status': status,
        'notes_length': len(notes) if notes else 0,
    }
    audit_logger.info(f"Alert Reviewed: {json.dumps(audit_data, ensure_ascii=False)}")

