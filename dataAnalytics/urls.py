from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name='landing'),
    path("loading/", views.cacheData, name='fillingCache'),
    path("landing/", views.viewDescriptive, name='firstView'),

    path("csvDownload/", views.downloadCubeCSV ,name="csvDownload")
]