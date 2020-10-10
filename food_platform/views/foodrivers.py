from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.template import RequestContext

from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView
from django.http import HttpResponse
from ..decorators import foodriver_required
from ..forms import FoodriverAreaForm, FoodriverSignUpForm, TakePickupForm
from ..models import Pickup, Foodriver, TakenPickup, CustomUser, Interested_area
import os


class FoodriverSignUpView(CreateView):
    model = CustomUser
    form_class = FoodriverSignUpForm
    #template_name = 'registration/signup_form.html'

    def get(self, *args, **kwards):
        form = FoodriverSignUpForm
        return render(self.request, 'registration/signup_form.html', {'form': form})
    #def get_context_data(self, **kwargs):
#        ''' New user'''
    #    kwargs['user_type'] = 'foodriver'
    #    print("Before getting context")
#        context = super().get_context_data(**kwargs)
    #    print(context)
#        return context

    def post(self, request, **kwards):
        print("Files",  request)
        form = FoodriverSignUpForm(request.POST, request.FILES)
        context = {}
        if form.is_valid():
            user = form.save()
            login(self.request, user, backend='food_platform.models.EmailAuth')
            return redirect('foodrivers:pickup_list')
        else:
            context['form'] = form
            return render(self.request, 'registration/signup_form.html', context)

    #def form_valid(self, form):
#        ''' Logging In'''#
    #    user = form.save()
    #    login(self.request, user)
    #    return redirect('foodrivers:pickup_list')


@method_decorator([login_required, foodriver_required], name='dispatch')
class FoodriverAreaView(UpdateView):
    model = Foodriver
    form_class = FoodriverAreaForm
    template_name = 'food_platform/foodrivers/area_form.html'
    success_url = reverse_lazy('foodrivers:pickup_list')

    def get_object(self):
        return self.request.user.foodriver

    def form_valid(self, form):
        messages.success(self.request, 'Area updated with success!')
        return super().form_valid(form)


@method_decorator([login_required, foodriver_required], name='dispatch')
class PickupListView(ListView):
    model = Pickup
    ordering = ('name', )
    context_object_name = 'pickups'
    template_name = 'food_platform/foodrivers/pickup_list.html'

    def get_queryset(self):
        foodriver = self.request.user.foodriver
        foodriver_area = foodriver.area.values_list('pk', flat=True)
        taken_pickups = foodriver.pickups.values_list('pk', flat=True)
        # ??
        queryset = Pickup.objects.filter(interested_area__in=foodriver_area) \
            .exclude(pk__in=taken_pickups) \
            .annotate(pickup_times_count=Count('pickup_times')) \
            .filter(pickup_times_count__gt=0)
        return queryset


@method_decorator([login_required, foodriver_required], name='dispatch')
class TakenPickupListView(ListView):
    model = TakenPickup
    context_object_name = 'taken_pickups'
    template_name = 'food_platform/foodrivers/taken_pickup_list.html'

    def get_queryset(self):
        queryset = self.request.user.foodriver.taken_pickups.select_related('pickup', 'pickup__interested_area').order_by('pickup__name')
        # CHANGE SUBJECT FOR URGENCY
        # PUT THIS .order_by('pickup__interested_area')
        # .select_related('pickup', 'pickup__interested_area') \
        # .order_by('pickup__name')
        return queryset


@login_required
@foodriver_required
def take_pickup(request, pk):
    pickup = get_object_or_404(Pickup, pk=pk)
    foodriver = request.user.foodriver

    if foodriver.pickups.filter(pk=pk).exists():
        return render(request, 'foodrivers/taken_pickup.html')
    # this is a comment: questions=pickup_times
    total_pickup_times = pickup.pickup_times.count()
    unanswered_pickup_times = foodriver.get_unanswered_pickup_times(pickup)
    total_unanswered_pickup_times = unanswered_pickup_times.count()
    progress = 100 - round(((total_unanswered_pickup_times - 1) / total_pickup_times) * 100)
    pickup_time = unanswered_pickup_times.first()

    if request.method == 'POST':
        form = TakePickupForm(pickup_time=pickup_time, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                foodriver_answer = form.save(commit=False)
                foodriver_answer.foodriver = foodriver
                foodriver_answer.save()
                if foodriver.get_unanswered_pickup_times(pickup).exists():
                    return redirect('foodrivers:take_pickup', pk)
                else:
                    correct_answers = foodriver.pickup_answers.filter(answer__pickup_time__pickup=pickup, answer__is_correct=True).count()
                    score = round((correct_answers / total_pickup_times) * 100.0, 2)
                    TakenPickup.objects.create(foodriver=foodriver, pickup=pickup, score=score)
                    if score < 50.0:
                        messages.warning(request, 'Better luck next time! Your score for the pickup %s was %s.' % (pickup.name, score))
                    else:
                        messages.success(request, 'Congratulations! You completed the pickup %s with success! You scored %s points.' % (pickup.name, score))
                    return redirect('foodrivers:pickup_list')
    else:
        form = TakePickupForm(pickup_time=pickup_time)

    return render(request, 'food_platform/foodrivers/take_pickup_form.html', {
        'pickup': pickup,
        'pickup_time': pickup_time,
        'form': form,
        'progress': progress
    })


@login_required
def login_view_profile(request):
    user = request.user
    args = {'user': user, 'areas': user.foodriver.area.all()}
    #print(user.profile_Image.path)
    return render(request, 'food_platform/foodrivers/foodrivers_login_user_profile.html', args)


@login_required
def view_profile(request, pk=None):
    user = CustomUser.objects.get(pk=pk)
    args = {'user': user, 'areas': user.areas.objects.get(user=user)}
    return render(request, 'food_platform/foodrivers/foodrivers_user_profile.html', args)
