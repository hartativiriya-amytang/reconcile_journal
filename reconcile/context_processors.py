from .models import ReconciliationConfig, ReconciliationSession, ReconciliationRule, ReconciliationResult


def dashboard_stats(request):
    return {
        'dashboard_configs': ReconciliationConfig.objects.count(),
        'dashboard_sessions': ReconciliationSession.objects.count(),
        'dashboard_rules': ReconciliationRule.objects.count(),
        'dashboard_results': ReconciliationResult.objects.count(),
        'dashboard_recent_sessions': ReconciliationSession.objects.select_related('config').order_by('-created_at')[:10],
    }
