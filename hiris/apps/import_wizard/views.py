import logging
app_log = logging.getLogger('app')

from django.conf import settings
from django.views.generic.base import View
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import UploadFileForImport

class ManageImports(View):
    ''' The starting place for importing.  Show information on imports, started imports, new import, etc. '''
    def get(self, request, *args, **kwargs):
        ''' Handle a get request.  Returns a starting import page. '''
        importers: list[dict] = []

        # Bring in the importers from settings
        for importer, importer_dict in settings.IMPORT_WIZARD['Importers'].items():
            importer_item: dict = {
                'name': importer_dict.get('long_name', importer_dict['name']),
                'importer': importer, # Used for URLs
            }

            if description := importer_dict.get('description'): importer_item['description'] = description

            importers.append(importer_item)

        return render(request, "import_manager.django-html", {'importers': importers})

class NewImport(View):
    ''' View for creating a new import '''
    def get(self, request, *args, **kwargs):
        ''' Build a new Import '''
        
        form = UploadFileForImport();

        return render(request, "new_import.django-html", {'form': UploadFileForImport(), 'importer': settings.IMPORT_WIZARD['Importers'][kwargs['importer_slug']]['name']})
    
    def post(self, request, *args, **kwargs):
        ''' Get the file for a new import '''
        app_log.info('getting file?')
        form = UploadFileForImport(request.POST, request.FILES)

        # for filename, file in request.FILES.items():
        #     app_log.info(request.FILES[filename].name)

        if form.is_valid():
            with open('/hiris-files/' + request.FILES['file'].name, 'wb+') as destination:
                for chunk in request.FILES['file'].chunks():
                    destination.write(chunk)

            return HttpResponseRedirect(reverse('Import_Wizard:do_import'))

        else:
            # Needs to have a better error
            return HttpResponseRedirect(reverse('Import_Wizard:do_import'))


class DoImport(View):
    ''' Do the actual import stuff '''
    def get(self, request, *args, **kwargs):
        ''' Dothe actual import stuff '''
        
        return render(request, 'do_import.django-html')