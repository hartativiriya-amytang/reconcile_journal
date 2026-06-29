from django.urls import path
from . import views

app_name = 'reconcile'

urlpatterns = [
    path('', views.index, name='index'),
    path('configure/', views.configure_fields, name='configure_fields'),
    path('upload/', views.upload_files, name='upload_files'),
    path('results/<int:session_id>/', views.view_results, name='view_results'),
    path('download/matched/<int:session_id>/', views.download_matched, name='download_matched'),
    path('download/unmatched/<int:session_id>/', views.download_unmatched, name='download_unmatched'),
    path('download/summary/<int:session_id>/', views.download_summary, name='download_summary'),
    path('api/config-status/', views.get_config_status, name='get_config_status'),
]