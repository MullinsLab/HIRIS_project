from django.contrib.auth.decorators import login_required
from django.urls import path, include

from hiris.apps.import_wizard.views import ManageImports, NewImportScheme, DoImport

app_name='import_wizard'

urlpatterns = [
    path('', ManageImports.as_view(), name='import'),
    path('<slug:importer_slug>', NewImportScheme.as_view(), name='new_import'),
    path('<int:import_scheme_id>', DoImport.as_view(), name='do_import'),
]