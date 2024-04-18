import logging
log = logging.getLogger('app')


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, Group

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy

from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView

from hiris.apps.core import forms

    
class UsersList(LoginRequiredMixin, TemplateView):
    """ Control who can access the data """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """ The basic page """

        return render(request, "admin/user_list.html")
    

class UserUpdate(LoginRequiredMixin, UpdateView):
    """ Handles requests for editing a scientist """

    model = User
    template_name = 'admin/user_form.html'
    # form_class = ScientistForm

    # success_url = reverse_lazy("viroserve:scientist")
    

class UserCreate(LoginRequiredMixin, CreateView):
    """ Handles requests for creating a scientist """

    model = User
    template_name = 'admin/user_form.html'
    form_class = forms.UserForm

    success_url = reverse_lazy("admin:user_list")