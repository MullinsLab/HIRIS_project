import logging
logger = logging.getLogger('app')

from django.conf import settings
from django.views.generic.base import View
from django.shortcuts import render

class ImportManager(View):
    ''' The starting place for importing.  Show information on imports, started imports, new import, etc. '''
    def get(self, request, *args, **kwargs):
        ''' Handle a get request.  Returns a starting import page. '''
        importers = []

        # Bring in the importers from settings
        for importer in settings.IMPORT_WIZARD['Importers']:
            logger.info(importer)
            importer_item = {'name' : importer.get('long_name', importer['name'])}
            if description := importer.get('description'): importer_item['description'] = description

            importers.append(importer_item)

        return render(request, "start_import.django-html", {'importers': importers})