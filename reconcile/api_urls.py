from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'configs', api_views.ReconciliationConfigViewSet)
router.register(r'fields', api_views.ReconciliationFieldViewSet)
router.register(r'mappings', api_views.FieldMappingViewSet)
router.register(r'rules', api_views.ReconciliationRuleViewSet)
router.register(r'sessions', api_views.ReconciliationSessionViewSet)
router.register(r'results', api_views.ReconciliationResultViewSet)

urlpatterns = [
    path('', api_views.api_overview, name='api-overview'),
    path('bulk-configure/', api_views.bulk_configure, name='api-bulk-configure'),
    path('reconcile/', api_views.run_reconciliation, name='api-reconcile'),
    path('', include(router.urls)),
]
