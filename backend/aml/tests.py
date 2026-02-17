"""
Tests for AML System
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta

from .models import Customer, Transaction, Rule, Alert, RiskScore, Report
from .services.transaction_monitor import get_transaction_monitor
from .services.risk_scorer import get_risk_scorer
from .services.alert_generator import get_alert_generator
from .services.report_generator import get_report_generator
from .rules.aml_rules import get_rule_engine


class HealthReadyTest(TestCase):
    """Test health and readiness endpoints (no auth)."""

    def setUp(self):
        self.client = Client()

    def test_health_returns_ok(self):
        r = self.client.get('/api/health/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'ok')
        self.assertIn('service', r.json())

    def test_ready_returns_ready_when_db_ok(self):
        r = self.client.get('/api/ready/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'ready')
        self.assertEqual(r.json()['database'], 'ok')


class CustomerModelTest(TestCase):
    """Test Customer model"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
    
    def test_customer_creation(self):
        """Test customer creation"""
        self.assertEqual(self.customer.customer_id, 'CUST001')
        self.assertEqual(self.customer.first_name, 'John')
        self.assertEqual(self.customer.current_risk_level, 'MEDIUM')
        self.assertEqual(self.customer.risk_score, Decimal('50.0'))


class TransactionModelTest(TestCase):
    """Test Transaction model"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
        
        self.transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('1000000'),
            currency='IRR',
            status='COMPLETED'
        )
    
    def test_transaction_creation(self):
        """Test transaction creation"""
        self.assertEqual(self.transaction.transaction_id, 'TXN001')
        self.assertEqual(self.transaction.customer, self.customer)
        self.assertEqual(self.transaction.amount, Decimal('1000000'))
        self.assertFalse(self.transaction.is_suspicious)


class RuleEngineTest(TestCase):
    """Test Rule Engine"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
        
        # Create a threshold rule
        self.rule = Rule.objects.create(
            name='High Amount Threshold',
            description='Flag transactions above 10M',
            rule_type='THRESHOLD',
            status='ACTIVE',
            configuration={
                'amount_threshold': 10000000
            },
            priority=1
        )
    
    def test_threshold_rule(self):
        """Test threshold rule evaluation"""
        # Create a high amount transaction
        transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('15000000'),  # Above threshold
            currency='IRR',
            status='COMPLETED'
        )
        
        rule_engine = get_rule_engine()
        triggered_rules, reasons, risk_score = rule_engine.evaluate_transaction(transaction)
        
        self.assertGreater(len(triggered_rules), 0)
        self.assertIn(self.rule, triggered_rules)
        self.assertGreater(risk_score, 0)


class RiskScorerTest(TestCase):
    """Test Risk Scorer"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
    
    def test_transaction_risk_scoring(self):
        """Test transaction risk score calculation"""
        transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('50000000'),  # High amount
            currency='IRR',
            status='COMPLETED'
        )
        
        risk_scorer = get_risk_scorer()
        result = risk_scorer.calculate_transaction_risk_score(transaction)
        
        self.assertIn('score', result)
        self.assertIn('factors', result)
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)
    
    def test_customer_risk_scoring(self):
        """Test customer risk score calculation"""
        risk_scorer = get_risk_scorer()
        result = risk_scorer.calculate_customer_risk_score(self.customer)
        
        self.assertIn('score', result)
        self.assertIn('factors', result)
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)


class TransactionMonitorTest(TestCase):
    """Test Transaction Monitor"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
        
        # Create a threshold rule
        Rule.objects.create(
            name='High Amount Threshold',
            description='Flag transactions above 10M',
            rule_type='THRESHOLD',
            status='ACTIVE',
            configuration={
                'amount_threshold': 10000000
            },
            priority=1
        )
    
    def test_transaction_monitoring(self):
        """Test transaction monitoring"""
        transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('15000000'),  # Above threshold
            currency='IRR',
            status='COMPLETED'
        )
        
        monitor = get_transaction_monitor()
        result = monitor.monitor_transaction(transaction)
        
        self.assertIn('risk_score', result)
        self.assertIn('is_suspicious', result)
        self.assertIn('should_alert', result)
        
        # Refresh transaction from DB
        transaction.refresh_from_db()
        self.assertIsNotNone(transaction.risk_score)
        
        # Check if alert was created
        if result['should_alert']:
            alerts = Alert.objects.filter(transaction=transaction)
            self.assertGreater(alerts.count(), 0)


class AlertGeneratorTest(TestCase):
    """Test Alert Generator"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
        
        self.transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('15000000'),
            currency='IRR',
            status='COMPLETED'
        )
    
    def test_alert_generation(self):
        """Test alert generation"""
        alert_generator = get_alert_generator()
        
        alert = alert_generator.generate_alert(
            transaction=self.transaction,
            triggered_rules=[],
            risk_score=Decimal('85'),
            severity='HIGH',
            reasons=['High transaction amount']
        )
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.transaction, self.transaction)
        self.assertEqual(alert.customer, self.customer)
        self.assertEqual(alert.severity, 'HIGH')
        self.assertEqual(alert.status, 'OPEN')
    
    def test_alert_review(self):
        """Test alert review"""
        alert_generator = get_alert_generator()
        
        alert = alert_generator.generate_alert(
            transaction=self.transaction,
            triggered_rules=[],
            risk_score=Decimal('85'),
            severity='HIGH',
            reasons=['High transaction amount']
        )
        
        reviewed_alert = alert_generator.review_alert(
            alert=alert,
            reviewer='test_user',
            status='RESOLVED',
            notes='False positive - legitimate business transaction'
        )
        
        self.assertEqual(reviewed_alert.status, 'RESOLVED')
        self.assertEqual(reviewed_alert.reviewed_by, 'test_user')
        self.assertIsNotNone(reviewed_alert.reviewed_at)


class ReportGeneratorTest(TestCase):
    """Test Report Generator"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
        
        self.transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('15000000'),
            currency='IRR',
            status='COMPLETED'
        )
        
        self.alert = Alert.objects.create(
            alert_id='ALT001',
            transaction=self.transaction,
            customer=self.customer,
            severity='HIGH',
            status='OPEN',
            title='Test Alert',
            description='Test alert description',
            risk_score=Decimal('85')
        )
    
    def test_sar_generation(self):
        """Test SAR report generation"""
        report_generator = get_report_generator()
        
        period_start = timezone.now() - timedelta(days=30)
        period_end = timezone.now()
        
        report = report_generator.generate_sar(
            alerts=[self.alert],
            period_start=period_start,
            period_end=period_end,
            submitted_by='test_user'
        )
        
        self.assertIsNotNone(report)
        self.assertEqual(report.report_type, 'SAR')
        self.assertEqual(report.status, 'DRAFT')
        self.assertIn('alerts', report.report_data)
        self.assertEqual(len(report.report_data['alerts']), 1)
    
    def test_ctr_generation(self):
        """Test CTR report generation"""
        report_generator = get_report_generator()
        
        period_start = timezone.now() - timedelta(days=30)
        period_end = timezone.now()
        
        report = report_generator.generate_ctr(
            transactions=[self.transaction],
            period_start=period_start,
            period_end=period_end,
            threshold=Decimal('10000000'),
            submitted_by='test_user'
        )
        
        self.assertIsNotNone(report)
        self.assertEqual(report.report_type, 'CTR')
        self.assertEqual(report.status, 'DRAFT')
        self.assertIn('transactions', report.report_data)
        self.assertEqual(len(report.report_data['transactions']), 1)

