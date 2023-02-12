from django.views.generic.base import View
from django.shortcuts import render

class StartImport(View):
    def get(self, request, *args, **kwargs):
        return render(request, "start_import.html")