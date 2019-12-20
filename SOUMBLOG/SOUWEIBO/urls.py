from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_interface, name='search_interface'),
    path('update', views.update_data, name='update_data'),
    path('search/<str:words>/<int:page>', views.search, name='search'),
]