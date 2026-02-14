"""
AML System Models
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Customer(models.Model):
    """
    Customer model for KYC data and customer information
    """
    CUSTOMER_TYPES = [
        ('INDIVIDUAL', 'Individual'),
        ('BUSINESS', 'Business'),
        ('INSTITUTION', 'Institution'),
    ]
    
    RISK_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.CharField(max_length=100, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='INDIVIDUAL')
    
    # KYC Information
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=50, blank=True, db_index=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='IR')
    
    # Registration
    registration_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    # Risk Assessment
    current_risk_level = models.CharField(max_length=20, choices=RISK_LEVELS, default='MEDIUM')
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=50.0,
                                     validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_id']),
            models.Index(fields=['email']),
            models.Index(fields=['current_risk_level']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"


class Transaction(models.Model):
    """
    Transaction model for financial transactions
    """
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER', 'Transfer'),
        ('PAYMENT', 'Payment'),
        ('REFUND', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction Details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='IRR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Parties
    sender_account = models.CharField(max_length=100, blank=True)
    receiver_account = models.CharField(max_length=100, blank=True)
    receiver_name = models.CharField(max_length=200, blank=True)
    receiver_country = models.CharField(max_length=100, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    transaction_date = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Risk Assessment
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                      validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_suspicious = models.BooleanField(default=False)
    flagged_reasons = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['customer', 'transaction_date']),
            models.Index(fields=['is_suspicious']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.customer.customer_id} - {self.amount} {self.currency}"


class Rule(models.Model):
    """
    AML Rules that can be configured and applied to transactions
    """
    RULE_TYPES = [
        ('THRESHOLD', 'Threshold-based'),
        ('PATTERN', 'Pattern-based'),
        ('BEHAVIORAL', 'Behavioral'),
        ('GEOGRAPHIC', 'Geographic'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('DRAFT', 'Draft'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Rule Configuration (stored as JSON for flexibility)
    configuration = models.JSONField(default=dict)
    
    # Priority and Scoring
    priority = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    risk_weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0,
                                      validators=[MinValueValidator(0), MaxValueValidator(10)])
    
    # Metadata
    created_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_applied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['priority', '-created_at']
        indexes = [
            models.Index(fields=['status', 'rule_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.rule_type})"


class Alert(models.Model):
    """
    Alert model for suspicious transaction alerts
    """
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('UNDER_REVIEW', 'Under Review'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
        ('ESCALATED', 'Escalated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_id = models.CharField(max_length=100, unique=True, db_index=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='alerts')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='alerts')
    
    # Alert Details
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Rule Information
    triggered_rules = models.ManyToManyField(Rule, related_name='alerts', blank=True)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2,
                                      validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Review Information
    reviewed_by = models.CharField(max_length=100, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_id']),
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.alert_id} - {self.title} ({self.severity})"


class RiskScore(models.Model):
    """
    Risk Score model for tracking customer risk scores over time
    """
    SCORE_TYPES = [
        ('CUSTOMER', 'Customer Risk Score'),
        ('TRANSACTION', 'Transaction Risk Score'),
        ('AGGREGATE', 'Aggregate Risk Score'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='risk_scores')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='risk_scores')
    
    score_type = models.CharField(max_length=20, choices=SCORE_TYPES, default='CUSTOMER')
    score = models.DecimalField(max_digits=5, decimal_places=2,
                                 validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Score Breakdown
    factors = models.JSONField(default=dict)  # Store individual risk factors
    calculation_method = models.CharField(max_length=100, blank=True)
    
    # Metadata
    calculated_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['customer', 'calculated_at']),
            models.Index(fields=['score_type']),
        ]
    
    def __str__(self):
        return f"{self.customer.customer_id} - {self.score_type} - {self.score}"


class Report(models.Model):
    """
    Regulatory Report model (SAR, CTR, etc.)
    """
    REPORT_TYPES = [
        ('SAR', 'Suspicious Activity Report'),
        ('CTR', 'Currency Transaction Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('GENERATED', 'Generated'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_id = models.CharField(max_length=100, unique=True, db_index=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Report Content
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_data = models.JSONField(default=dict)  # Structured report data
    
    # Related Entities
    related_alerts = models.ManyToManyField(Alert, related_name='reports', blank=True)
    related_transactions = models.ManyToManyField(Transaction, related_name='reports', blank=True)
    related_customers = models.ManyToManyField(Customer, related_name='reports', blank=True)
    
    # File Storage
    file_path = models.CharField(max_length=500, blank=True)
    file_format = models.CharField(max_length=10, default='JSON')  # JSON, CSV, PDF
    
    # Submission
    submitted_by = models.CharField(max_length=100, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    regulatory_body = models.CharField(max_length=200, blank=True)
    
    # Metadata
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_id']),
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.report_id} - {self.report_type} - {self.status}"

