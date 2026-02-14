"""
Transaction Monitoring Service
Monitors and processes transactions in real-time
"""
import logging
import uuid
from decimal import Decimal
from typing import Dict, Optional
from django.utils import timezone

from aml.models import Transaction, Customer, RiskScore
from aml.rules.aml_rules import get_rule_engine
from aml.services.risk_scorer import get_risk_scorer
from aml.services.alert_generator import get_alert_generator

logger = logging.getLogger('aml')


class TransactionMonitor:
    """
    Service for monitoring and processing transactions
    """
    
    def __init__(self):
        self.rule_engine = get_rule_engine()
        self.risk_scorer = get_risk_scorer()
    
    def monitor_transaction(self, transaction: Transaction) -> Dict:
        """
        Monitor a transaction and apply AML rules and risk scoring
        
        Args:
            transaction: Transaction object to monitor
            
        Returns:
            Dict with monitoring results including alerts, risk scores, etc.
        """
        logger.info(f"Monitoring transaction {transaction.transaction_id}")
        
        try:
            # Step 1: Evaluate rules
            triggered_rules, rule_reasons, rule_risk_score = self.rule_engine.evaluate_transaction(transaction)
            
            # Step 2: Calculate transaction risk score
            risk_result = self.risk_scorer.calculate_transaction_risk_score(
                transaction, 
                rule_risk_score=rule_risk_score
            )
            
            # Step 3: Update transaction with risk information
            transaction.risk_score = risk_result['score']
            transaction.is_suspicious = len(triggered_rules) > 0 or risk_result['score'] >= Decimal('70')
            transaction.flagged_reasons = rule_reasons
            transaction.save()
            
            # Step 4: Save risk score record
            RiskScore.objects.create(
                customer=transaction.customer,
                transaction=transaction,
                score_type='TRANSACTION',
                score=risk_result['score'],
                factors=risk_result['factors'],
                calculation_method=risk_result['method']
            )
            
            # Step 5: Update customer risk score if needed
            self._update_customer_risk_score(transaction.customer)
            
            # Step 6: Determine if alert should be generated
            should_alert = self._should_generate_alert(transaction, triggered_rules, risk_result['score'])
            alert_severity = self._determine_alert_severity(risk_result['score'], len(triggered_rules))
            
            # Step 7: Generate alert if needed
            alert = None
            if should_alert:
                alert_generator = get_alert_generator()
                alert = alert_generator.generate_alert(
                    transaction=transaction,
                    triggered_rules=triggered_rules,
                    risk_score=risk_result['score'],
                    severity=alert_severity,
                    reasons=rule_reasons
                )
            
            result = {
                'transaction_id': transaction.transaction_id,
                'risk_score': float(risk_result['score']),
                'is_suspicious': transaction.is_suspicious,
                'triggered_rules': [rule.name for rule in triggered_rules],
                'rule_reasons': rule_reasons,
                'risk_factors': risk_result['factors'],
                'should_alert': should_alert,
                'alert_severity': alert_severity,
                'alert_id': alert.alert_id if alert else None,
            }
            
            logger.info(f"Transaction {transaction.transaction_id} monitored. Risk: {risk_result['score']}, "
                       f"Suspicious: {transaction.is_suspicious}, Rules triggered: {len(triggered_rules)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error monitoring transaction {transaction.transaction_id}: {str(e)}")
            raise
    
    def _should_generate_alert(self, transaction: Transaction, 
                                triggered_rules: list, 
                                risk_score: Decimal) -> bool:
        """
        Determine if an alert should be generated for this transaction
        """
        # Generate alert if:
        # 1. Risk score is high (>= 70)
        # 2. Any rules were triggered
        # 3. Transaction is marked as suspicious
        
        if risk_score >= Decimal('70'):
            return True
        
        if len(triggered_rules) > 0:
            return True
        
        if transaction.is_suspicious:
            return True
        
        return False
    
    def _determine_alert_severity(self, risk_score: Decimal, rules_triggered: int) -> str:
        """
        Determine alert severity based on risk score and rules triggered
        """
        if risk_score >= Decimal('90') or rules_triggered >= 3:
            return 'CRITICAL'
        elif risk_score >= Decimal('80') or rules_triggered >= 2:
            return 'HIGH'
        elif risk_score >= Decimal('70') or rules_triggered >= 1:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _update_customer_risk_score(self, customer: Customer):
        """
        Update customer's overall risk score based on recent transactions
        """
        try:
            # Calculate new customer risk score
            customer_risk_result = self.risk_scorer.calculate_customer_risk_score(customer)
            
            # Update customer risk score
            customer.risk_score = customer_risk_result['score']
            
            # Update risk level based on score
            if customer_risk_result['score'] >= Decimal('80'):
                customer.current_risk_level = 'CRITICAL'
            elif customer_risk_result['score'] >= Decimal('60'):
                customer.current_risk_level = 'HIGH'
            elif customer_risk_result['score'] >= Decimal('40'):
                customer.current_risk_level = 'MEDIUM'
            else:
                customer.current_risk_level = 'LOW'
            
            customer.save()
            
            # Save risk score record
            RiskScore.objects.create(
                customer=customer,
                score_type='CUSTOMER',
                score=customer_risk_result['score'],
                factors=customer_risk_result['factors'],
                calculation_method=customer_risk_result['method']
            )
            
            logger.info(f"Updated customer {customer.customer_id} risk score to {customer_risk_result['score']}")
            
        except Exception as e:
            logger.error(f"Error updating customer risk score for {customer.customer_id}: {str(e)}")
    
    def process_batch_transactions(self, transactions: list) -> Dict:
        """
        Process multiple transactions in batch
        
        Args:
            transactions: List of Transaction objects
            
        Returns:
            Dict with batch processing results
        """
        results = {
            'processed': 0,
            'suspicious': 0,
            'alerts_generated': 0,
            'errors': 0,
            'details': []
        }
        
        for transaction in transactions:
            try:
                result = self.monitor_transaction(transaction)
                results['processed'] += 1
                
                if result['is_suspicious']:
                    results['suspicious'] += 1
                
                if result['should_alert']:
                    results['alerts_generated'] += 1
                
                results['details'].append({
                    'transaction_id': transaction.transaction_id,
                    'risk_score': result['risk_score'],
                    'is_suspicious': result['is_suspicious']
                })
                
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Error processing transaction {transaction.transaction_id}: {str(e)}")
        
        logger.info(f"Batch processing completed: {results['processed']} processed, "
                   f"{results['suspicious']} suspicious, {results['alerts_generated']} alerts")
        
        return results


# Singleton instance
_transaction_monitor_instance = None

def get_transaction_monitor() -> TransactionMonitor:
    """Get singleton instance of TransactionMonitor"""
    global _transaction_monitor_instance
    if _transaction_monitor_instance is None:
        _transaction_monitor_instance = TransactionMonitor()
    return _transaction_monitor_instance

