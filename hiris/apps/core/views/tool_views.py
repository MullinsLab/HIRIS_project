import logging
log = logging.getLogger('app')

from django.views.generic.base import View
from django.shortcuts import render
from django.contrib.auth import authenticate, login

from hiris.apps.core.utils.db import get_environments_count, get_genes_count
from hiris.apps.core.utils.simple import underscore_keys

class Home(View):
    ''' The default view for HIRIS Home.  Currently shows the About page '''
    
    def get(self, request, *args, **kwargs):
        ''' Returns the default template on a get '''
        return render(request, "about.html")

    def post(self, request, *args, **kwargs):
        ''' Recieves the username and password for login '''
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)

        return render(request, "about.html")
    
class DataSources(View):
    """ View to show the data sources in the database """

    def get(self, request, *args, **kwargs):
        """ Show the page """

        counts: dict = underscore_keys(get_environments_count())

        gene_count: int = get_genes_count()
        return render(request, "data_sources.html", context={"counts": counts, "gene_count": gene_count})