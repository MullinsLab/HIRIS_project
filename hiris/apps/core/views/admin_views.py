import logging
log = logging.getLogger('app')


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, Group

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy

from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, FormView

from hiris.utils import StaffRequiredMixin
from hiris.apps.core import forms
from hiris.apps.core.models import DataSet

    
class UsersList(StaffRequiredMixin, TemplateView):
    """ Lists the users for editing """

    template_name = "admin/user_list.html"
    

class UserUpdate(StaffRequiredMixin, UpdateView):
    """ Handles requests for editing a scientist """

    model = User
    template_name = 'admin/user_form.html'
    form_class = forms.UserForm

    success_url = reverse_lazy("admin:user_list")
    

class UserCreate(StaffRequiredMixin, CreateView):
    """ Handles requests for creating a scientist """

    model = User
    template_name = 'admin/user_form.html'
    form_class = forms.UserForm

    success_url = reverse_lazy("admin:user_list")


class UserPassword(StaffRequiredMixin, FormView):
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
    
    
class GroupsList(StaffRequiredMixin, TemplateView):
    """ Lists the groups for editing """

    template_name = 'admin/group_list.html'
    

class GroupUpdate(StaffRequiredMixin, UpdateView):
    """ Handles requests for editing a group """

    model = Group
    template_name = 'admin/group_form.html'
    fields = ["name"]

    success_url = reverse_lazy("admin:group_list")


class GroupCreate(StaffRequiredMixin, CreateView):
    """ Handles requests for creating a group """

    model = Group
    template_name = 'admin/group_form.html'
    fields = ["name"]

    success_url = reverse_lazy("admin:group_list")


class DataSetAccessList(StaffRequiredMixin, TemplateView):
    """ Handles requests for viewing and editing dataset permissions """

    options: dict = {"Anonymous": "Anonymous users", "Everyone": "All logged in users", "Specific": "Specific users or groups"}

    template_name = "admin/dataset_access_list.html"
    extra_context = {"data_sets": DataSet.objects.all(), "options": options}
