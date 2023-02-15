import logging
logger = logging.getLogger('app')

from django.conf import settings
from django.views.generic.base import View
from django.shortcuts import render
from django.utils.text import slugify

class ManageImports(View):
    ''' The starting place for importing.  Show information on imports, started imports, new import, etc. '''
    def get(self, request, *args, **kwargs):
        ''' Handle a get request.  Returns a starting import page. '''
        importers: list[dict] = []

        # Bring in the importers from settings
        for importer in settings.IMPORT_WIZARD['Importers']:
            importer_item: dict = {
                'name': importer.get('long_name', importer['name']),
                'slug': slugify(importer['name']), # Used for URLs
            }

            if description := importer.get('description'): importer_item['description'] = description

            importers.append(importer_item)

        return render(request, "import_manager.django-html", {'importers': importers})

class NewImport(View):
    ''' View for creating a new import '''
    def get(self, request, *args, **kwargs):
        ''' Build a new Import '''
        return render(request, "new_import.django-html")