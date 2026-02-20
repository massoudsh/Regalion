"""
Django Admin configuration for AML models.
Custom AdminSite with dashboard (counts, recent alerts); filters, actions, list display.
"""
from django.contrib import admin
from .models import Customer, Transaction, Alert, RiskScore, Rule, Report


# --- Custom AdminSite with dashboard (counts + recent alerts) ---

class AMLAdminSite(admin.AdminSite):
    site_header = 'Regalion AML'
    site_title = 'Regalion AML Admin'
    index_title = 'Overview'

    index_template = 'admin/aml_index.html'

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        from .models import Customer, Transaction, Alert, Rule
        extra_context['aml_customers_count'] = Customer.objects.count()
        extra_context['aml_transactions_count'] = Transaction.objects.count()
        extra_context['aml_alerts_open_count'] = Alert.objects.filter(status='OPEN').count()
        extra_context['aml_rules_count'] = Rule.objects.count()
        extra_context['aml_recent_alerts'] = Alert.objects.select_related(
            'customer', 'transaction'
        ).order_by('-created_at')[:10]
        return super().index(request, extra_context)


aml_admin_site = AMLAdminSite(name='aml_admin')


# --- Admin actions ---

def mark_alerts_resolved(modeladmin, request, queryset):
    updated = queryset.update(status='RESOLVED', reviewed_by=request.user.get_username())
    modeladmin.message_user(request, f'{updated} alert(s) marked as Resolved.')


mark_alerts_resolved.short_description = 'Mark selected as Resolved'


def mark_alerts_false_positive(modeladmin, request, queryset):
    updated = queryset.update(status='FALSE_POSITIVE', reviewed_by=request.user.get_username())
    modeladmin.message_user(request, f'{updated} alert(s) marked as False Positive.')


mark_alerts_false_positive.short_description = 'Mark selected as False Positive'


def escalate_alerts(modeladmin, request, queryset):
    updated = queryset.update(status='ESCALATED', reviewed_by=request.user.get_username())
    modeladmin.message_user(request, f'{updated} alert(s) escalated.')


escalate_alerts.short_description = 'Escalate selected alerts'


def set_customer_risk_high(modeladmin, request, queryset):
    updated = queryset.update(current_risk_level='HIGH')
    modeladmin.message_user(request, f'{updated} customer(s) set to High risk.')


set_customer_risk_high.short_description = 'Set risk level to High'


def set_customer_risk_critical(modeladmin, request, queryset):
    updated = queryset.update(current_risk_level='CRITICAL')
    modeladmin.message_user(request, f'{updated} customer(s) set to Critical risk.')


set_customer_risk_critical.short_description = 'Set risk level to Critical'


def activate_rules(modeladmin, request, queryset):
    updated = queryset.update(status='ACTIVE')
    modeladmin.message_user(request, f'{updated} rule(s) activated.')


activate_rules.short_description = 'Activate selected rules'


def deactivate_rules(modeladmin, request, queryset):
    updated = queryset.update(status='INACTIVE')
    modeladmin.message_user(request, f'{updated} rule(s) deactivated.')


deactivate_rules.short_description = 'Deactivate selected rules'


# --- ModelAdmins (registered on aml_admin_site) ---

class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'customer_id', 'first_name', 'last_name', 'email', 'current_risk_level',
        'risk_score', 'customer_type', 'registration_date', 'is_active'
    )
    list_filter = ('customer_type', 'current_risk_level', 'is_active', 'country')
    search_fields = ('customer_id', 'first_name', 'last_name', 'email', 'national_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 25
    actions = [set_customer_risk_high, set_customer_risk_critical]


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'customer', 'transaction_type', 'amount', 'currency',
        'status', 'risk_score', 'is_suspicious', 'transaction_date'
    )
    list_filter = ('transaction_type', 'status', 'is_suspicious', 'currency')
    search_fields = ('transaction_id', 'customer__customer_id', 'sender_account', 'receiver_account')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-transaction_date',)
    date_hierarchy = 'transaction_date'
    list_per_page = 25
    list_select_related = ('customer',)


class RuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'status', 'priority', 'risk_weight', 'created_at')
    list_filter = ('rule_type', 'status')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_applied_at')
    ordering = ('priority', '-created_at')
    list_per_page = 25
    actions = [activate_rules, deactivate_rules]


class AlertAdmin(admin.ModelAdmin):
    list_display = (
        'alert_id', 'customer', 'transaction', 'severity', 'status',
        'risk_score', 'created_at', 'reviewed_by'
    )
    list_filter = ('severity', 'status', 'created_at')
    search_fields = ('alert_id', 'customer__customer_id', 'transaction__transaction_id', 'title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    filter_horizontal = ('triggered_rules',)
    list_per_page = 25
    list_select_related = ('customer', 'transaction')
    actions = [mark_alerts_resolved, mark_alerts_false_positive, escalate_alerts]


class RiskScoreAdmin(admin.ModelAdmin):
    list_display = ('customer', 'transaction', 'score_type', 'score', 'calculated_at')
    list_filter = ('score_type', 'calculated_at')
    search_fields = ('customer__customer_id', 'transaction__transaction_id')
    readonly_fields = ('id', 'created_at')
    ordering = ('-calculated_at',)
    date_hierarchy = 'calculated_at'
    list_per_page = 25
    list_select_related = ('customer', 'transaction')


class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'report_id', 'report_type', 'status', 'title', 'created_at',
        'submitted_at', 'submitted_by'
    )
    list_filter = ('report_type', 'status', 'file_format')
    search_fields = ('report_id', 'title', 'regulatory_body')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    filter_horizontal = ('related_alerts', 'related_transactions', 'related_customers')
    list_per_page = 25


# Register all models with the custom AML admin site
aml_admin_site.register(Customer, CustomerAdmin)
aml_admin_site.register(Transaction, TransactionAdmin)
aml_admin_site.register(Rule, RuleAdmin)
aml_admin_site.register(Alert, AlertAdmin)
aml_admin_site.register(RiskScore, RiskScoreAdmin)
aml_admin_site.register(Report, ReportAdmin)
