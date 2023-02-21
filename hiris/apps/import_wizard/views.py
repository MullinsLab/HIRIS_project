import logging
log = logging.getLogger('app')

from django.conf import settings
from django.views.generic.base import View
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import UploadFileForImport
from .models import ImportScheme, ImportFile


class ManageImports(LoginRequiredMixin, View):
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


class NewImport(LoginRequiredMixin, View):
    ''' View for creating a new import '''

    def get(self, request, *args, **kwargs):
        ''' Build a new Import '''
        
        form = UploadFileForImport()
        importer = kwargs['importer_slug']

        return render(request, "new_import.django-html", {'form': UploadFileForImport(), 'importer': settings.IMPORT_WIZARD['Importers'][importer]['name']})
    
    def post(self, request, *args, **kwargs):
        ''' Get the file for a new import '''

        form = UploadFileForImport(request.POST, request.FILES)
        importer = kwargs['importer_slug']
        file = request.FILES['file']

        log.debug(f'Getting file: {file.name}')

        if form.is_valid():
            new_import_scheme = ImportScheme(name=file.name, importer=importer, user=request.user)
            new_import_scheme.save()
            log.debug(f'Stored ImportScheme with PKey of {new_import_scheme.id}')

            new_import_file = ImportFile(name=file.name, import_scheme=new_import_scheme)
            new_import_file.save()
            log.debug(f'Stored ImportFile with PKey of {new_import_file.id}')

            # Save the file named from the file_name of the ImportFile
            log.debug(f'Getting ready to store file at: {settings.WORKING_FILES_DIR}{new_import_file.file_name}')
            with open(settings.WORKING_FILES_DIR + new_import_file.file_name, 'wb+') as destination:
                for chunk in file.chunks():
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