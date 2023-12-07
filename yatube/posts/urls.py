from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index),
    path('groups/', views.groups),
    path("group/<slug:slug>/", views.group_details, name="group_list")
]