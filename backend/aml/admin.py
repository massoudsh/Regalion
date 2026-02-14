"""
Django Admin configuration for AML models
"""
from django.contrib import admin
from .models import Customer, Transaction, Alert, RiskScore, Rule, Report


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'first_name', 'last_name', 'email', 'current_risk_level', 
                    'risk_score', 'registration_date', 'is_active')
    list_filter = ('customer_type', 'current_risk_level', 'is_active', 'country')
    search_fields = ('customer_id', 'first_name', 'last_name', 'email', 'national_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'customer', 'transaction_type', 'amount', 'currency',
                    'status', 'risk_score', 'is_suspicious', 'transaction_date')
    list_filter = ('transaction_type', 'status', 'is_suspicious', 'currency')
    search_fields = ('transaction_id', 'customer__customer_id', 'sender_account', 'receiver_account')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-transaction_date',)
    date_hierarchy = 'transaction_date'


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'status', 'priority', 'risk_weight', 'created_at')
    list_filter = ('rule_type', 'status')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_applied_at')
    ordering = ('priority', '-created_at')


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_id', 'customer', 'transaction', 'severity', 'status', 
                    'risk_score', 'created_at', 'reviewed_by')
    list_filter = ('severity', 'status', 'created_at')
    search_fields = ('alert_id', 'customer__customer_id', 'transaction__transaction_id', 'title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    filter_horizontal = ('triggered_rules',)


@admin.register(RiskScore)
class RiskScoreAdmin(admin.ModelAdmin):
    list_display = ('customer', 'transaction', 'score_type', 'score', 'calculated_at')
    list_filter = ('score_type', 'calculated_at')
    search_fields = ('customer__customer_id', 'transaction__transaction_id')
    readonly_fields = ('id', 'created_at')
    ordering = ('-calculated_at',)
    date_hierarchy = 'calculated_at'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'report_type', 'status', 'title', 'created_at', 
                    'submitted_at', 'submitted_by')
    list_filter = ('report_type', 'status', 'file_format')
    search_fields = ('report_id', 'title', 'regulatory_body')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    filter_horizontal = ('related_alerts', 'related_transactions', 'related_customers')

