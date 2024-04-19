import logging
log = logging.getLogger('app')


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, Group

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy

from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, FormView

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
    form_class = forms.UserForm

    success_url = reverse_lazy("admin:user_list")
    

class UserCreate(LoginRequiredMixin, CreateView):
    """ Handles requests for creating a scientist """

    model = User
    template_name = 'admin/user_form.html'
    form_class = forms.UserForm

    success_url = reverse_lazy("admin:user_list")


class UserPassword(LoginRequiredMixin, FormView):
    """ Handles requests for setting a scientist's user password """

    form_class = forms.UserPasswordForm
    template_name: str = "admin/user_password_form.html"
    success_url = reverse_lazy("admin:user_list")

    def get_context_data(self, **kwargs):
        """ Add the user to the context """

        context: dict = super().get_context_data(**kwargs)
        context["user"] = User.objects.get(pk=self.kwargs.get("pk"))
        return context
    
    def get_initial(self):
        """ Set the initial data for the form """

        initial: dict = super().get_initial()
        initial["user_id"] = self.kwargs.get("pk")

        return initial
    
    def form_valid(self, form):
        """ Save the form and redirect to the success url """

        log.debug("Form is valid")
        form.save()
        return super().form_valid(form)  
    
    def form_invalid(self, form):
        log.debug("Form is invalid")
        return super().form_invalid(form)
    
    def post(self, request, *args, **kwargs):
        log.debug("Post")
        return super().post(request, *args, **kwargs)