# quiz = pickup
# question = pickup_time
# answer= answer


from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from ..decorators import foodonator_required
from ..forms import BaseAnswerInlineFormSet, PickupTimeForm, FoodonatorSignUpForm
from ..models import Answer, PickupTime, Pickup, CustomUser
# Question = PickupTime


class FoodonatorSignUpView(CreateView):
    model = CustomUser
    form_class = FoodonatorSignUpForm
    template_name = 'registration/signup_form.html'

    def get(self, *args, **kwards):
        form = FoodonatorSignUpForm
        return render(self.request, self.template_name, {'form': form})

    def post(self, request, **kwards):
        print("Files",  request)
        form = FoodonatorSignUpForm(request.POST, request.FILES)
        context = {}
        if form.is_valid():
            user = form.save()
            login(self.request, user, backend='food_platform.models.EmailAuth')
            return redirect('foodonators:pickup_change_list')
        else:
            context['form'] = form
            return render(self.request, self.template_name, context)

    # def get_context_data(self, **kwargs):
    #     kwargs['user_type'] = 'foodonator'
    #     return super().get_context_data(**kwargs)
    #
    # def form_valid(self, form):
    #     user = form.save()
    #     login(self.request, user, backend='food_platform.models.EmailAuth')
    #     return redirect('foodonators:pickup_change_list')


@method_decorator([login_required, foodonator_required], name='dispatch')
class PickupListView(ListView):
    model = Pickup
    ordering = ('name', )
    context_object_name = 'pickups'
    template_name = 'food_platform/foodonators/pickup_change_list.html'

    def get_queryset(self):
        queryset = self.request.user.pickups.select_related('interested_area') .annotate(pickup_times_count=Count('pickup_times', distinct=True)) .annotate(taken_count=Count('taken_pickups', distinct=True))
        #CHANGE THIS FOR interested_area.select_related('interested_area') \
        # .select_related('interested_area') \.annotate(pickup_times_count=Count('pickup_times', distinct=True)) \.annotate(taken_count=Count('taken_pickups', distinct=True))
        return queryset

@method_decorator([login_required, foodonator_required], name='dispatch')
class PickupCreateView(CreateView):
    model = Pickup
    #CHANGE THIS FOR interested_area
    fields = ('name', 'interested_area', )
    template_name = 'food_platform/foodonators/pickup_add_form.html'

    def form_valid(self, form):
        pickup = form.save(commit=False)
        pickup.owner = self.request.user
        pickup.save()
        messages.success(self.request, 'The pickup was created with success! Go ahead and add some pickup_times now.')
        return redirect('foodonators:pickup_change', pickup.pk)

@method_decorator([login_required, foodonator_required], name='dispatch')
class PickupUpdateView(UpdateView):
    model = Pickup
    #CHANGE THIS FOR interested_area
    fields = ('name', 'interested_area', )
    context_object_name = 'pickup'
    template_name = 'food_platform/foodonators/pickup_change_form.html'

    def get_context_data(self, **kwargs):
        kwargs['pickup_times'] = self.get_object().pickup_times.annotate(answers_count=Count('answers'))
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing pickups that belongs
        to the logged in user.
        '''
        return self.request.user.pickups.all()

    def get_success_url(self):
        return reverse('foodonators:pickup_change', kwargs={'pk': self.object.pk})

@method_decorator([login_required, foodonator_required], name='dispatch')
class PickupDeleteView(DeleteView):
    model = Pickup
    context_object_name = 'pickup'
    template_name = 'food_platform/foodonators/pickup_delete_confirm.html'
    success_url = reverse_lazy('foodonators:pickup_change_list')

    def delete(self, request, *args, **kwargs):
        pickup = self.get_object()
        messages.success(request, 'The pickup %s was deleted with success!' % pickup.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.pickups.all()

@method_decorator([login_required, foodonator_required], name='dispatch')
class PickupResultsView(DetailView):
    model = Pickup
    context_object_name = 'pickup'
    template_name = 'food_platform/foodonators/pickup_results.html'

    def get_context_data(self, **kwargs):
        pickup = self.get_object()
        taken_pickups = pickup.taken_pickups.select_related('foodriver__user').order_by('-date')
        total_taken_pickups = taken_pickups.count()
        pickup_score = pickup.taken_pickups.aggregate(average_score=Avg('score'))
        extra_context = {
            'taken_pickups': taken_pickups,
            'total_taken_pickups': total_taken_pickups,
            'pickup_score': pickup_score
        }
        kwargs.update(extra_context)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.pickups.all()

@login_required
@foodonator_required
def pickup_time_add(request, pk):
    # By filtering the quiz by the url keyword argument `pk` and
    # by the owner, which is the logged in user, we are protecting
    # this view at the object-level. Meaning only the owner of
    # quiz will be able to add questions to it.
    pickup = get_object_or_404(Pickup, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = PickupTimeForm(request.POST)
        if form.is_valid():
            pickup_time = form.save(commit=False)
            pickup_time.pickup = pickup
            pickup_time.save()
            messages.success(request, 'You may now add answers/options to the pickup_time.')
            return redirect('foodonators:pickup_time_change', pickup.pk, pickup_time.pk)
    else:
        form = PickupTimeForm()

    return render(request, 'food_platform/foodonators/pickup_time_add_form.html', {'pickup': pickup, 'form': form})

@login_required
@foodonator_required
def pickup_time_change(request, pickup_pk, pickup_time_pk):
    # Simlar to the `question_add` view, this view is also managing
    # the permissions at object-level. By querying both `quiz` and
    # `question` we are making sure only the owner of the quiz can
    # change its details and also only questions that belongs to this
    # specific quiz can be changed via this url (in cases where the
    # user might have forged/player with the url params.
    pickup = get_object_or_404(Pickup, pk=pickup_pk, owner=request.user)
    pickup_time = get_object_or_404(PickupTime, pk=pickup_time_pk, pickup=pickup)

    AnswerFormSet = inlineformset_factory(
        PickupTime,  # parent model
        Answer,  # base model
        formset=BaseAnswerInlineFormSet,
        fields=('text', 'is_correct'),
        min_num=2,
        validate_min=True,
        max_num=10,
        validate_max=True
    )

    if request.method == 'POST':
        form = PickupTimeForm(request.POST, instance=pickup_time)
        formset = AnswerFormSet(request.POST, instance=pickup_time)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, 'Pickup time and answers saved with success!')
            return redirect('foodonators:pickup_change', pickup.pk)
    else:
        form = PickupTimeForm(instance=pickup_time)
        formset = AnswerFormSet(instance=pickup_time)

    return render(request, 'food_platform/foodonators/pickup_time_change_form.html', {
        'pickup': pickup,
        'pickup_time': pickup_time,
        'form': form,
        'formset': formset
    })


@method_decorator([login_required, foodonator_required], name='dispatch')
class PickupTimeDeleteView(DeleteView):
    model = PickupTime
    context_object_name = 'pickup_time'
    template_name = 'food_platform/foodonators/pickup_time_delete_confirm.html'
    pk_url_kwarg = 'pickup_time_pk'

    def get_context_data(self, **kwargs):
        pickup_time = self.get_object()
        kwargs['pickup'] = pickup_time.pickup
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        pickup_time = self.get_object()
        messages.success(request, 'The pickup_time %s was deleted with success!' % pickup_time.text)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return PickupTime.objects.filter(pickup__owner=self.request.user)

    def get_success_url(self):
        pickup_time = self.get_object()
        return reverse('foodonators:pickup_change', kwargs={'pk': pickup_time.pickup_id})


def login_view_profile(request):
    user = request.user
    args = {'user': user}
    return render(request, 'food_platform/foodonators/foodonators_login_user_profile.html', args)


def view_profile(request, pk=None):
    user = CustomUser.objects.get(pk=pk)
    args = {'user': user}
    return render(request, 'food_platform/foodonators/foodonators_user_profile.html', args)
