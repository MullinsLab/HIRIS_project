# Create your views here.
from django.views.generic.base import View
from django.shortcuts import render

class About(View):
    def get(self, request, *args, **kwargs):
        return render(request, "about.html")
