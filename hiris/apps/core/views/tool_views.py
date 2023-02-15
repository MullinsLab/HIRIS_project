import logging
logger = logging.getLogger('app')

from django.views.generic.base import View
from django.shortcuts import render
from django.contrib.auth import authenticate, login


class Home(View):
    ''' The default view for HIRIS Home.  Currently shows the About page '''
    def get(self, request, *args, **kwargs):
        ''' Returns the default template on a get '''
        return render(request, "about.django-html")


    def post(self, request, *args, **kwargs):
        ''' Recieves the username and password for login '''
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
        # logger.info(request.POST)

        return render(request, "about.django-html")