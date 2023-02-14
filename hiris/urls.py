from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', include('hiris.apps.core.urls.tool_urls', namespace='core')),
    path('api/', include('hiris.apps.core.urls.api_urls', namespace='api')),
    path('import/', include('hiris.apps.import_wizard.urls', namespace='import')),
    path('export/', include('hiris.apps.export_wizard.urls', namespace='export')),

    # For UW_SAML
    re_path(r'^saml/', include('uw_saml.urls')),

    # For debug_toolbar
    path('__debug__/', include('debug_toolbar.urls')),
]
