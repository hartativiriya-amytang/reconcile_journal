from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from reconcile.admin import admin_site

urlpatterns = [
    path('', lambda request: redirect('admin/')),
    path('admin/', admin_site.urls),
    path('api/', include('reconcile.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
