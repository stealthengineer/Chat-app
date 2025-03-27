from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('', views.index, name='index'),
    path('chat/<str:room_name>/', views.room, name='room'),
]
