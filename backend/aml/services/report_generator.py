"""
Report Generator Service
Generates regulatory reports (SAR, CTR, etc.)
"""
import logging
import uuid
import json
import csv
import os
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from django.utils import timezone
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from aml.models import Report, Alert, Transaction, Customer

logger = logging.getLogger('aml')


class ReportGenerator:
    """
    Service for generating regulatory reports
    """
    
    def __init__(self):
        self.reports_dir = os.path.join(settings.BASE_DIR, 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_sar(self, alerts: List[Alert], 
                    period_start: datetime,
                    period_end: datetime,
                    submitted_by: str = '') -> Report:
        """
        Generate Suspicious Activity Report (SAR)
        
        Args:
            alerts: List of alerts to include in the report
            period_start: Start of reporting period
            period_end: End of reporting period
            submitted_by: Username of person submitting the report
            
        Returns:
            Created Report object
        """
        logger.info(f"Generating SAR report for {len(alerts)} alerts")
        
        # Generate report ID
        report_id = f"SAR-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Prepare report data
        report_data = {
            'report_type': 'SAR',
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'alerts_count': len(alerts),
            'alerts': []
        }
        
        # Add alert details
        for alert in alerts:
            alert_data = {
                'alert_id': alert.alert_id,
                'transaction_id': alert.transaction.transaction_id,
                'customer_id': alert.customer.customer_id,
                'customer_name': f"{alert.customer.first_name} {alert.customer.last_name}",
                'amount': str(alert.transaction.amount),
                'currency': alert.transaction.currency,
                'severity': alert.severity,
                'risk_score': str(alert.risk_score),
                'description': alert.description,
                'created_at': alert.created_at.isoformat(),
            }
            report_data['alerts'].append(alert_data)
        
        # Create report object
        report = Report.objects.create(
            report_id=report_id,
            report_type='SAR',
            status='DRAFT',
            title=f"Suspicious Activity Report - {period_start.date()} to {period_end.date()}",
            description=f"SAR report containing {len(alerts)} suspicious activities",
            report_data=report_data,
            period_start=period_start,
            period_end=period_end,
            submitted_by=submitted_by
        )
        
        # Link related entities
        report.related_alerts.set(alerts)
        report.related_transactions.set([alert.transaction for alert in alerts])
        report.related_customers.set([alert.customer for alert in alerts])
        
        logger.info(f"SAR report {report_id} created")
        
        return report
    
    def generate_ctr(self, transactions: List[Transaction],
                    period_start: datetime,
                    period_end: datetime,
                    threshold: Decimal = Decimal('100000000'),
                    submitted_by: str = '') -> Report:
        """
        Generate Currency Transaction Report (CTR)
        
        Args:
            transactions: List of transactions to include
            period_start: Start of reporting period
            period_end: End of reporting period
            threshold: Amount threshold for CTR
            submitted_by: Username of person submitting the report
            
        Returns:
            Created Report object
        """
        logger.info(f"Generating CTR report for {len(transactions)} transactions")
        
        # Generate report ID
        report_id = f"CTR-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Prepare report data
        report_data = {
            'report_type': 'CTR',
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'threshold': str(threshold),
            'transactions_count': len(transactions),
            'total_amount': str(sum(t.amount for t in transactions)),
            'transactions': []
        }
        
        # Add transaction details
        for transaction in transactions:
            transaction_data = {
                'transaction_id': transaction.transaction_id,
                'customer_id': transaction.customer.customer_id,
                'customer_name': f"{transaction.customer.first_name} {transaction.customer.last_name}",
                'amount': str(transaction.amount),
                'currency': transaction.currency,
                'transaction_type': transaction.transaction_type,
                'transaction_date': transaction.transaction_date.isoformat(),
                'receiver_account': transaction.receiver_account,
                'receiver_country': transaction.receiver_country,
            }
            report_data['transactions'].append(transaction_data)
        
        # Create report object
        report = Report.objects.create(
            report_id=report_id,
            report_type='CTR',
            status='DRAFT',
            title=f"Currency Transaction Report - {period_start.date()} to {period_end.date()}",
            description=f"CTR report for transactions exceeding {threshold} threshold",
            report_data=report_data,
            period_start=period_start,
            period_end=period_end,
            submitted_by=submitted_by
        )
        
        # Link related entities
        report.related_transactions.set(transactions)
        report.related_customers.set([t.customer for t in transactions])
        
        logger.info(f"CTR report {report_id} created")
        
        return report
    
    def export_report_json(self, report: Report) -> str:
        """
        Export report to JSON file
        
        Args:
            report: Report object to export
            
        Returns:
            Path to generated JSON file
        """
        filename = f"{report.report_id}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report.report_data, f, indent=2, ensure_ascii=False)
        
        report.file_path = filepath
        report.file_format = 'JSON'
        report.save()
        
        logger.info(f"Report {report.report_id} exported to JSON: {filepath}")
        
        return filepath
    
    def export_report_csv(self, report: Report) -> str:
        """
        Export report to CSV file
        
        Args:
            report: Report object to export
            
        Returns:
            Path to generated CSV file
        """
        filename = f"{report.report_id}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            if report.report_type == 'SAR':
                writer.writerow([
                    'Alert ID', 'Transaction ID', 'Customer ID', 'Customer Name',
                    'Amount', 'Currency', 'Severity', 'Risk Score', 'Created At'
                ])
                
                # Write data
                for alert_data in report.report_data.get('alerts', []):
                    writer.writerow([
                        alert_data.get('alert_id', ''),
                        alert_data.get('transaction_id', ''),
                        alert_data.get('customer_id', ''),
                        alert_data.get('customer_name', ''),
                        alert_data.get('amount', ''),
                        alert_data.get('currency', ''),
                        alert_data.get('severity', ''),
                        alert_data.get('risk_score', ''),
                        alert_data.get('created_at', ''),
                    ])
            
            elif report.report_type == 'CTR':
                writer.writerow([
                    'Transaction ID', 'Customer ID', 'Customer Name',
                    'Amount', 'Currency', 'Type', 'Date', 'Receiver Account', 'Receiver Country'
                ])
                
                # Write data
                for transaction_data in report.report_data.get('transactions', []):
                    writer.writerow([
                        transaction_data.get('transaction_id', ''),
                        transaction_data.get('customer_id', ''),
                        transaction_data.get('customer_name', ''),
                        transaction_data.get('amount', ''),
                        transaction_data.get('currency', ''),
                        transaction_data.get('transaction_type', ''),
                        transaction_data.get('transaction_date', ''),
                        transaction_data.get('receiver_account', ''),
                        transaction_data.get('receiver_country', ''),
                    ])
        
        report.file_path = filepath
        report.file_format = 'CSV'
        report.save()
        
        logger.info(f"Report {report.report_id} exported to CSV: {filepath}")
        
        return filepath
    
    def export_report_pdf(self, report: Report) -> str:
        """
        Export report to PDF file
        
        Args:
            report: Report object to export
            
        Returns:
            Path to generated PDF file
        """
        filename = f"{report.report_id}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>{report.title}</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Report metadata
        metadata = [
            ['Report ID:', report.report_id],
            ['Report Type:', report.report_type],
            ['Period:', f"{report.period_start.date()} to {report.period_end.date()}"],
            ['Status:', report.status],
            ['Created:', report.created_at.strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        if report.submitted_by:
            metadata.append(['Submitted By:', report.submitted_by])
        
        metadata_table = Table(metadata, colWidths=[150, 300])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        # Report data
        if report.report_type == 'SAR':
            story.append(Paragraph("<b>Suspicious Activities:</b>", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # Alert table
            alert_data = [['Alert ID', 'Customer', 'Amount', 'Severity', 'Risk Score']]
            
            for alert_data_item in report.report_data.get('alerts', [])[:50]:  # Limit to 50 for PDF
                alert_data.append([
                    alert_data_item.get('alert_id', '')[:20],
                    alert_data_item.get('customer_name', '')[:30],
                    f"{alert_data_item.get('amount', '')} {alert_data_item.get('currency', '')}",
                    alert_data_item.get('severity', ''),
                    alert_data_item.get('risk_score', ''),
                ])
            
            alert_table = Table(alert_data, colWidths=[100, 150, 100, 80, 80])
            alert_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(alert_table)
        
        elif report.report_type == 'CTR':
            story.append(Paragraph("<b>Currency Transactions:</b>", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # Transaction summary
            summary_data = [
                ['Total Transactions:', str(report.report_data.get('transactions_count', 0))],
                ['Total Amount:', f"{report.report_data.get('total_amount', '0')} {report.report_data.get('transactions', [{}])[0].get('currency', '')}"],
            ]
            
            summary_table = Table(summary_data, colWidths=[200, 200])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        
        report.file_path = filepath
        report.file_format = 'PDF'
        report.save()
        
        logger.info(f"Report {report.report_id} exported to PDF: {filepath}")
        
        return filepath
    
    def submit_report(self, report: Report, regulatory_body: str = '') -> Report:
        """
        Submit a report to regulatory body
        
        Args:
            report: Report to submit
            regulatory_body: Name of regulatory body
            
        Returns:
            Updated Report object
        """
        report.status = 'SUBMITTED'
        report.submitted_at = timezone.now()
        if regulatory_body:
            report.regulatory_body = regulatory_body
        report.save()
        
        logger.info(f"Report {report.report_id} submitted to {regulatory_body}")
        
        return report


# Singleton instance
_report_generator_instance = None

def get_report_generator() -> ReportGenerator:
    """Get singleton instance of ReportGenerator"""
    global _report_generator_instance
    if _report_generator_instance is None:
        _report_generator_instance = ReportGenerator()
    return _report_generator_instance

