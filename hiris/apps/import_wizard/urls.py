from django.contrib.auth.decorators import login_required
from django.urls import path, include

from hiris.apps.import_wizard.views import ManageImports, NewImport

app_name='hiris.apps.import_wizard'

urlpatterns = [
    path('', ManageImports.as_view(), name='import'),
    path('new/<importer_slug>', NewImport.as_view(), name='new_import')
]