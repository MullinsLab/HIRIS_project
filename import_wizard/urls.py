from django.contrib.auth.decorators import login_required
from django.urls import path, include

from import_wizard.views import ManageImports, NewImportScheme, DoImportScheme, DoImportSchemeItem, ListImportSchemeItems

app_name='import_wizard'

urlpatterns = [
    path('', ManageImports.as_view(), name='import'),
    path('<int:import_scheme_id>', DoImportScheme.as_view(), name='scheme'),
    path('<int:import_scheme_id>/list', ListImportSchemeItems.as_view(), name='scheme_list_items'),
    path('<int:import_scheme_id>/<int:import_item_id>', DoImportSchemeItem.as_view(), name='scheme_item'),
    path('<slug:importer_slug>', NewImportScheme.as_view(), name='new_scheme'),
]