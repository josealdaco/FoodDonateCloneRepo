from django.contrib import admin
from django.urls import include, path
from food_platform.views import food_platform, foodrivers, foodonators, shelters
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('food_platform.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', food_platform.SignUpView.as_view(), name='signup'),
    path('accounts/signup/foodriver/', foodrivers.FoodriverSignUpView.as_view(), name='foodriver_signup'),
    path('accounts/signup/foodonator/', foodonators.FoodonatorSignUpView.as_view(), name='foodonator_signup'),
    path('accounts/signup/shelters/', shelters.ShelterSignUpView.as_view(), name='shelter_signup'),

    # Password reset links (ref: https://github.com/django/django/blob/master/django/contrib/auth/views.py)
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), 
        name='password_change_done'),

    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html'), 
        name='password_change'),

    path('password_reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_done.html'),
     name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
     name='password_reset_complete'),
]
