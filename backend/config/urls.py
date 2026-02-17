"""
URL configuration for Regalion AML System.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.schemas import get_schema_view
from rest_framework.permissions import AllowAny
from aml.views import dashboard_view

schema_view = get_schema_view(
    title='Regalion AML API',
    description='API for customers, transactions, alerts, rules, reports, and risk scores.',
    version='1.0',
    permission_classes=[AllowAny],
)

urlpatterns = [
    path('', dashboard_view),
    path('admin/', admin.site.urls),
    path('api/schema/', schema_view),
    path('api/', include('aml.urls')),
]

