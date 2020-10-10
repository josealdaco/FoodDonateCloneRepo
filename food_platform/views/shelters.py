from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView
from django.views import generic
from ..decorators import shelter_required
from ..forms import ShelterSignUpForm, ShelterInfoForm
from ..models import CustomUser, ShelterInfo
from django.http import HttpResponse, HttpResponseRedirect


class ShelterSignUpView(CreateView):
    model = CustomUser
    form_class = ShelterSignUpForm
    template_name = 'registration/signup_form.html'

    def get(self, *args, **kwards):
        form = ShelterSignUpForm
        return render(self.request, self.template_name, {'form': form})

    def post(self, request, **kwards):
        print("Files",  request)
        form = ShelterSignUpForm(request.POST, request.FILES)
        context = {}
        if form.is_valid():
            user = form.save()
            login(self.request, user, backend='food_platform.models.EmailAuth')
            return redirect('shelters:shelterinfo-list-project')
        else:
            context['form'] = form
            return render(self.request, self.template_name, context)

    # def get_context_data(self, **kwargs):
    #     kwargs['user_type'] = 'shelter'
    #     return super().get_context_data(**kwargs)
    #
    # def form_valid(self, form):
    #     user = form.save()
    #     login(self.request, user, backend='food_platform.models.EmailAuth')
    #     return redirect('shelters:shelterinfo-list-project')


class ShelterInfoListView(generic.ListView):
    """ Renders a list of all projects. """
    model = ShelterInfo

    def get(self, request):
        """ GET a list of projects. """
        shelterinfos = self.get_queryset().all()
        return render(request, 'food_platform/shelters/list.html', {
          'shelterinfos': shelterinfos
        })


class ShelterInfoDetailView(generic.DetailView):
    """ Renders a specific project based on it's slug."""
    model = ShelterInfo

    def get(self, request, slug):
        """ Returns a specific projects project by slug. """
        shelterinfo = self.get_queryset().get(slug__iexact=slug)
        return render(request, 'food_platform/shelters/shelterinfo.html', {
          'shelterinfo': shelterinfo
        })


class ShelterInfoCreateView(generic.CreateView):
    form_class = ShelterInfoForm
    template_name = "food_platform/shelters/new_shelterinfo.html"

    def post(self, request, *args, **kwargs):
        form = ShelterInfoForm(request.POST)
        if form.is_valid():
            project = form.save()
            project.save()
            return reverse_lazy("shelters:shelterinfo-details-project", args=[project.slug])
        else:
            print("RETURNED NONE")


class ShelterInfoUpdateView(generic.UpdateView):
    model = ShelterInfo
    fields = ['title', 'content']
    template_name = 'food_platform/shelters/new_shelterinfo.html'
