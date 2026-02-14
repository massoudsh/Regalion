"""
URL configuration for AML app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'alerts', views.AlertViewSet, basename='alert')
router.register(r'risk-scores', views.RiskScoreViewSet, basename='riskscore')
router.register(r'rules', views.RuleViewSet, basename='rule')
router.register(r'reports', views.ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]

