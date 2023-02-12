"""hiris URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', include('hiris.apps.core.urls.tool_urls', namespace='core')),
    path('api/', include('hiris.apps.core.urls.api_urls', namespace='api')),
    path('import/', include('hiris.apps.import_wizard.urls', namespace='import')),

    # For UW_SAML
    re_path(r'^saml/', include('uw_saml.urls')),

    # For debug_toolbar
    path('__debug__/', include('debug_toolbar.urls')),
]
