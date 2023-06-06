from django.contrib.auth.decorators import login_required
from django.urls import path, include

import logging
log = logging.getLogger('app')

from hiris.apps.core import views

# determine appname
app_name='tools'

urlpatterns = [
    path('', views.Home.as_view(), name='about'),
    path('datasources', views.DataSources.as_view(), name='data_sources'),
    path('top_genes', views.TopGenes.as_view(), name='top_genes'),
    path("summary-by-gene.js", views.SummaryByGeneJS.as_view(), name="summary_by_gene_js"),
    path("full-summary-by-gene.js", views.FullSummaryByGeneJS.as_view(), name="full_summary_by_gene_js"),
]
