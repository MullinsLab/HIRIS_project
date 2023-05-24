import logging
log = logging.getLogger('app')

from django.views.generic.base import View
from django.shortcuts import render
from django.contrib.auth import authenticate, login

from hiris.apps.core.utils.db import get_environments_count, get_genes_count, get_data_sources, get_summary_by_gene
from hiris.apps.core.utils.simple import underscore_keys, group_dict_list

class Home(View):
    ''' The default view for HIRIS Home.  Currently shows the About page '''
    
    def get(self, request, *args, **kwargs):
        ''' Returns the default template on a get '''

        summary_by_gene: list = get_summary_by_gene()
        log.debug(summary_by_gene[0])
        log.debug(f"Gene count: {len(summary_by_gene)}")

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
        data_sources: dict = underscore_keys(group_dict_list(dict_list=get_data_sources(), key="integration_environment_name"))

        gene_count: int = get_genes_count()
        return render(request, "data_sources.html", context={"counts": counts, "gene_count": gene_count, "data_sources": data_sources})
    
class SummaryByGeneJS(View):
    """ The JS file that holds the data for gene summaries """

    def get(self, request, *args, **kwargs):
        """ return the file """

        return render(request, "summary-by-gene.js", context={}, content_type="text/javascript")