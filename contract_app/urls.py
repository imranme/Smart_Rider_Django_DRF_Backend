from django.urls import path
from . import views

urlpatterns = [
    path('', views.ContractListView.as_view(), name='contract-list'),
]