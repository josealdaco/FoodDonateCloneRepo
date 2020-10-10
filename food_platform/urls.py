from django.urls import include, path

from .views import food_platform, foodrivers, foodonators, shelters
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', food_platform.home, name='home'),

    path('foodrivers/', include(([
        path('', foodrivers.PickupListView.as_view(), name='pickup_list'),
        path('user_profile/', foodrivers.login_view_profile, name='view-profile-page'),
        path('user_profile/<int:pk>', foodrivers.view_profile, name='view-profile-page-pk'),
        path('area/', foodrivers.FoodriverAreaView.as_view(), name='foodriver_area'),
        path('taken/', foodrivers.TakenPickupListView.as_view(), name='taken_pickup_list'),
        path('pickup/<int:pk>/', foodrivers.take_pickup, name='take_pickup'),
    ], 'food_platform'), namespace='foodrivers')),

    path('foodonators/', include(([
        path('', foodonators.PickupListView.as_view(), name='pickup_change_list'),
        path('user_profile/', foodonators.login_view_profile, name='view-profile-page'),
        path('user_profile/<int:pk>', foodonators.view_profile, name='view-profile-page-pk'),
        path('pickup/add/', foodonators.PickupCreateView.as_view(), name='pickup_add'),
        path('pickup/<int:pk>/', foodonators.PickupUpdateView.as_view(), name='pickup_change'),
        path('pickup/<int:pk>/delete/', foodonators.PickupDeleteView.as_view(), name='pickup_delete'),
        path('pickup/<int:pk>/results/', foodonators.PickupResultsView.as_view(), name='pickup_results'),
        path('pickup/<int:pk>/pickup_time/add/', foodonators.pickup_time_add, name='pickup_time_add'),
        path('pickup/<int:pickup_pk>/pickup_time/<int:pickup_time_pk>/', foodonators.pickup_time_change, name='pickup_time_change'),
        path('pickup/<int:pickup_pk>/pickup_time/<int:pickup_time_pk>/delete/', foodonators.PickupTimeDeleteView.as_view(), name='pickup_time_delete'),
    ], 'food_platform'), namespace='foodonators')),

    path('shelters/', include(([
        path('list_of_shelterinfos/', shelters.ShelterInfoListView.as_view(), name='shelterinfo-list-project'),
        path('new_shelterinfo/', shelters.ShelterInfoCreateView.as_view(), name='shelterinfo-create-project'),
        path('<str:slug>/', shelters.ShelterInfoDetailView.as_view(), name='shelterinfo-details-project'),
        path('edit/<int:pk>/', shelters.ShelterInfoUpdateView.as_view(), name='shelterinfo-update-project'),
    ], 'food_platform'), namespace='shelters')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
