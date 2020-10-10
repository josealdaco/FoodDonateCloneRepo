from django.shortcuts import redirect, render
from django.views.generic import TemplateView


class SignUpView(TemplateView):
    template_name = 'registration/signup.html'


def home(request):
    if request.user.is_authenticated:
        if request.user.is_foodonator:
            # change = update
            # pickup = quiz
            return redirect('foodonators:pickup_change_list')
        elif request.user.is_foodriver:
            return redirect('foodrivers:pickup_list')
        else:
            return redirect('shelters:shelterinfo-list-project')
    return render(request, 'food_platform/home.html')
