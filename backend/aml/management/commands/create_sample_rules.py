"""
Management command to create sample AML rules
"""
from django.core.management.base import BaseCommand
from aml.models import Rule


class Command(BaseCommand):
    help = 'Create sample AML rules for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample AML rules...')
        
        # Rule 1: High Amount Threshold
        rule1, created = Rule.objects.get_or_create(
            name='High Amount Threshold',
            defaults={
                'description': 'Flag transactions exceeding 10,000,000 IRR',
                'rule_type': 'THRESHOLD',
                'status': 'ACTIVE',
                'configuration': {
                    'amount_threshold': 10000000
                },
                'priority': 1,
                'risk_weight': 1.5,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule1.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule1.name}'))
        
        # Rule 2: Daily Transaction Count
        rule2, created = Rule.objects.get_or_create(
            name='Daily Transaction Count Threshold',
            defaults={
                'description': 'Flag customers with more than 20 transactions per day',
                'rule_type': 'THRESHOLD',
                'status': 'ACTIVE',
                'configuration': {
                    'daily_count_threshold': 20
                },
                'priority': 2,
                'risk_weight': 1.2,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule2.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule2.name}'))
        
        # Rule 3: Structuring Detection
        rule3, created = Rule.objects.get_or_create(
            name='Structuring Detection',
            defaults={
                'description': 'Detect potential structuring (multiple transactions just below threshold)',
                'rule_type': 'PATTERN',
                'status': 'ACTIVE',
                'configuration': {
                    'structuring_threshold': 10000000,
                    'structuring_count': 3,
                    'lookback_days': 7
                },
                'priority': 3,
                'risk_weight': 2.0,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule3.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule3.name}'))
        
        # Rule 4: Rapid Transactions
        rule4, created = Rule.objects.get_or_create(
            name='Rapid Transaction Detection',
            defaults={
                'description': 'Detect rapid successive transactions (potential layering)',
                'rule_type': 'PATTERN',
                'status': 'ACTIVE',
                'configuration': {
                    'rapid_transaction_threshold': True,
                    'rapid_transaction_minutes': 10,
                    'rapid_transaction_count': 5
                },
                'priority': 4,
                'risk_weight': 1.8,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule4.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule4.name}'))
        
        # Rule 5: Behavioral Change Detection
        rule5, created = Rule.objects.get_or_create(
            name='Behavioral Change Detection',
            defaults={
                'description': 'Detect sudden changes in transaction behavior',
                'rule_type': 'BEHAVIORAL',
                'status': 'ACTIVE',
                'configuration': {
                    'amount_increase_threshold': 3.0,
                    'lookback_days': 30,
                    'pattern_change_detection': True,
                    'pattern_change_threshold': 2.0
                },
                'priority': 5,
                'risk_weight': 1.5,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule5.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule5.name}'))
        
        # Rule 6: High-Risk Country
        rule6, created = Rule.objects.get_or_create(
            name='High-Risk Country Detection',
            defaults={
                'description': 'Flag transactions to high-risk countries',
                'rule_type': 'GEOGRAPHIC',
                'status': 'ACTIVE',
                'configuration': {
                    'high_risk_countries': ['XX', 'YY'],  # Replace with actual high-risk countries
                    'cross_border_threshold': 5000000
                },
                'priority': 6,
                'risk_weight': 1.3,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule6.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule6.name}'))
        
        self.stdout.write(self.style.SUCCESS('\nSample rules creation completed!'))

