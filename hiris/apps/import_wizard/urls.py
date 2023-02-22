from django.contrib.auth.decorators import login_required
from django.urls import path, include

from hiris.apps.import_wizard.views import ManageImports, NewImport, DoImport

app_name='Import_Wizard'

urlpatterns = [
    path('', ManageImports.as_view(), name='import'),
    path('new/<importer_slug>', NewImport.as_view(), name='new_import'),
    # path ('doimport/', DoImport.as_view(), name='do_import'),
    path ('<int:import_scheme_id>', DoImport.as_view(), name='do_import_with_id'),
]