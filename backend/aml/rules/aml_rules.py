"""
AML Rule Engine
Implements configurable rules for detecting suspicious transactions
"""
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncDay

from aml.models import Rule, Transaction, Customer

logger = logging.getLogger('aml')


class RuleEngine:
    """
    Main rule engine for evaluating AML rules against transactions
    """
    
    def __init__(self):
        self.active_rules = None
        self._load_rules()
    
    def _load_rules(self):
        """Load active rules from database"""
        self.active_rules = Rule.objects.filter(status='ACTIVE').order_by('priority')
        logger.info(f"Loaded {self.active_rules.count()} active rules")
    
    def evaluate_transaction(self, transaction: Transaction) -> Tuple[List[Rule], List[str], Decimal]:
        """
        Evaluate a transaction against all active rules
        
        Returns:
            Tuple of (triggered_rules, reasons, total_risk_score)
        """
        triggered_rules = []
        reasons = []
        total_risk_score = Decimal('0.0')
        
        if not self.active_rules.exists():
            logger.warning("No active rules found")
            return triggered_rules, reasons, total_risk_score
        
        for rule in self.active_rules:
            try:
                result = self._evaluate_rule(rule, transaction)
                if result['triggered']:
                    triggered_rules.append(rule)
                    reasons.append(result['reason'])
                    # Add weighted risk score
                    rule_risk = Decimal(str(result.get('risk_score', 0))) * rule.risk_weight
                    total_risk_score += rule_risk
                    logger.info(f"Rule '{rule.name}' triggered for transaction {transaction.transaction_id}")
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {str(e)}")
                continue
        
        return triggered_rules, reasons, total_risk_score
    
    def _evaluate_rule(self, rule: Rule, transaction: Transaction) -> Dict:
        """
        Evaluate a single rule against a transaction
        
        Returns:
            Dict with 'triggered', 'reason', and 'risk_score'
        """
        rule_type = rule.rule_type
        config = rule.configuration
        
        if rule_type == 'THRESHOLD':
            return self._evaluate_threshold_rule(rule, transaction, config)
        elif rule_type == 'PATTERN':
            return self._evaluate_pattern_rule(rule, transaction, config)
        elif rule_type == 'BEHAVIORAL':
            return self._evaluate_behavioral_rule(rule, transaction, config)
        elif rule_type == 'GEOGRAPHIC':
            return self._evaluate_geographic_rule(rule, transaction, config)
        else:
            logger.warning(f"Unknown rule type: {rule_type}")
            return {'triggered': False, 'reason': '', 'risk_score': 0}
    
    def _evaluate_threshold_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Evaluate threshold-based rules (amount, frequency, etc.)
        """
        triggered = False
        reason = ""
        risk_score = 0
        
        # Amount threshold
        if 'amount_threshold' in config:
            threshold = Decimal(str(config['amount_threshold']))
            if transaction.amount >= threshold:
                triggered = True
                reason = f"Transaction amount {transaction.amount} exceeds threshold {threshold}"
                risk_score = min(100, float(transaction.amount / threshold) * 50)
        
        # Daily transaction count threshold
        if 'daily_count_threshold' in config:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = Transaction.objects.filter(
                customer=transaction.customer,
                transaction_date__gte=today_start,
                status='COMPLETED'
            ).count()
            
            if today_count >= config['daily_count_threshold']:
                triggered = True
                reason = f"Daily transaction count {today_count} exceeds threshold {config['daily_count_threshold']}"
                risk_score = max(risk_score, min(100, (today_count / config['daily_count_threshold']) * 60))
        
        # Daily amount threshold
        if 'daily_amount_threshold' in config:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_total = Transaction.objects.filter(
                customer=transaction.customer,
                transaction_date__gte=today_start,
                status='COMPLETED'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            threshold = Decimal(str(config['daily_amount_threshold']))
            if today_total >= threshold:
                triggered = True
                reason = f"Daily transaction amount {today_total} exceeds threshold {threshold}"
                risk_score = max(risk_score, min(100, float(today_total / threshold) * 50))
        
        return {
            'triggered': triggered,
            'reason': reason,
            'risk_score': risk_score
        }
    
    def _evaluate_pattern_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Evaluate pattern-based rules (structuring, layering, etc.)
        """
        triggered = False
        reason = ""
        risk_score = 0
        
        # Structuring detection (multiple transactions just below threshold)
        if 'structuring_threshold' in config:
            threshold = Decimal(str(config['structuring_threshold']))
            # Check if transaction is just below threshold
            if threshold * Decimal('0.9') <= transaction.amount < threshold:
                # Check for multiple similar transactions
                lookback_days = config.get('lookback_days', 7)
                lookback_date = timezone.now() - timedelta(days=lookback_days)
                
                similar_transactions = Transaction.objects.filter(
                    customer=transaction.customer,
                    transaction_date__gte=lookback_date,
                    amount__gte=threshold * Decimal('0.9'),
                    amount__lt=threshold,
                    status='COMPLETED'
                ).count()
                
                if similar_transactions >= config.get('structuring_count', 3):
                    triggered = True
                    reason = f"Potential structuring: {similar_transactions} transactions just below threshold"
                    risk_score = min(100, similar_transactions * 20)
        
        # Rapid successive transactions (layering)
        if 'rapid_transaction_threshold' in config:
            minutes_threshold = config.get('rapid_transaction_minutes', 10)
            count_threshold = config.get('rapid_transaction_count', 5)
            
            time_threshold = timezone.now() - timedelta(minutes=minutes_threshold)
            recent_count = Transaction.objects.filter(
                customer=transaction.customer,
                transaction_date__gte=time_threshold,
                status='COMPLETED'
            ).count()
            
            if recent_count >= count_threshold:
                triggered = True
                reason = f"Rapid transactions: {recent_count} transactions in {minutes_threshold} minutes"
                risk_score = min(100, recent_count * 15)
        
        return {
            'triggered': triggered,
            'reason': reason,
            'risk_score': risk_score
        }
    
    def _evaluate_behavioral_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Evaluate behavioral rules (sudden behavior changes)
        """
        triggered = False
        reason = ""
        risk_score = 0
        
        customer = transaction.customer
        
        # Check for sudden increase in transaction amount
        if 'amount_increase_threshold' in config:
            # Get average transaction amount in last 30 days
            lookback_days = config.get('lookback_days', 30)
            lookback_date = timezone.now() - timedelta(days=lookback_days)
            
            avg_amount = Transaction.objects.filter(
                customer=customer,
                transaction_date__gte=lookback_date,
                transaction_date__lt=transaction.transaction_date,
                status='COMPLETED'
            ).aggregate(avg=Avg('amount'))['avg']
            
            if avg_amount:
                increase_ratio = float(transaction.amount / avg_amount)
                threshold_ratio = config.get('amount_increase_threshold', 3.0)
                
                if increase_ratio >= threshold_ratio:
                    triggered = True
                    reason = f"Sudden amount increase: {transaction.amount} vs avg {avg_amount:.2f} ({increase_ratio:.2f}x)"
                    risk_score = min(100, increase_ratio * 20)
        
        # Check for change in transaction pattern
        if 'pattern_change_detection' in config and config['pattern_change_detection']:
            # Compare last 7 days vs previous 7 days
            now = transaction.transaction_date
            recent_start = now - timedelta(days=7)
            previous_start = recent_start - timedelta(days=7)
            
            recent_count = Transaction.objects.filter(
                customer=customer,
                transaction_date__gte=recent_start,
                transaction_date__lt=now,
                status='COMPLETED'
            ).count()
            
            previous_count = Transaction.objects.filter(
                customer=customer,
                transaction_date__gte=previous_start,
                transaction_date__lt=recent_start,
                status='COMPLETED'
            ).count()
            
            if previous_count > 0:
                change_ratio = recent_count / previous_count
                if change_ratio >= config.get('pattern_change_threshold', 2.0):
                    triggered = True
                    reason = f"Transaction pattern change: {recent_count} vs {previous_count} transactions"
                    risk_score = max(risk_score, min(100, change_ratio * 25))
        
        return {
            'triggered': triggered,
            'reason': reason,
            'risk_score': risk_score
        }
    
    def _evaluate_geographic_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Evaluate geographic-based rules (high-risk countries, etc.)
        """
        triggered = False
        reason = ""
        risk_score = 0
        
        # High-risk countries
        high_risk_countries = config.get('high_risk_countries', [])
        if transaction.receiver_country in high_risk_countries:
            triggered = True
            reason = f"Transaction to high-risk country: {transaction.receiver_country}"
            risk_score = 70
        
        # Cross-border transaction threshold
        if 'cross_border_threshold' in config and transaction.receiver_country:
            if transaction.customer.country != transaction.receiver_country:
                threshold = Decimal(str(config['cross_border_threshold']))
                if transaction.amount >= threshold:
                    triggered = True
                    reason = f"Large cross-border transaction: {transaction.amount} from {transaction.customer.country} to {transaction.receiver_country}"
                    risk_score = max(risk_score, min(100, float(transaction.amount / threshold) * 40))
        
        return {
            'triggered': triggered,
            'reason': reason,
            'risk_score': risk_score
        }
    
    def reload_rules(self):
        """Reload rules from database"""
        self._load_rules()
        logger.info("Rules reloaded")


# Singleton instance
_rule_engine_instance = None

def get_rule_engine() -> RuleEngine:
    """Get singleton instance of RuleEngine"""
    global _rule_engine_instance
    if _rule_engine_instance is None:
        _rule_engine_instance = RuleEngine()
    return _rule_engine_instance

