from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from django.conf import settings

app_name='Base'

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', include('hiris.apps.core.urls.tool_urls', namespace='core')),
    path('api/', include('hiris.apps.core.urls.api_urls', namespace='api')),
    path('import/', include('ml_import_wizard.urls', namespace='ml_import_wizard')),
    path('export/', include('hiris.apps.export_wizard.urls', namespace='export_wizard')),

    # For login and logout
    path('login/', auth_views.LoginView.as_view(), name='login'),

    # For UW_SAML
    re_path(r'^saml/', include('uw_saml.urls')),

    # For debug_toolbar
    path('__debug__/', include('debug_toolbar.urls')),
]

if settings.LOGIN_TYPE == 'dual' or settings.LOGIN_TYPE == 'local':
    additional_settings =[
      path('login/', auth_views.LoginView.as_view(), name='login'),
      path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    ]
    urlpatterns += additional_settings