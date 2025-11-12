from django.urls import path
from . import views

urlpatterns = [
    # MAIN PAGES
    path("", views.index, name='landing'),
    path("yearRegistration/", views.inputYear, name='yearRegistration'),
    path("dataRegistration/", views.inputFootTraffic, name='dataRegistration'),
    path("ticketRegistration/", views.inputTicketData, name='ticketRegistration'),
    path("closingRegistration/", views.inputClosingData, name='closingRegistration'),
    path("missingLocationValues/", views.viewMissingDates, name='missingDates'),
    path("missingLocationValue/<str:pk>", views.viewDatesForLocation, name='missingDateFor'),
    path("csvDownload/<str:pk>", views.downloadMissingTraffic ,name="missingCSVDownload"),
    path("storageDownload/<str:pk>", views.downloadSelectedCSV ,name="downloadStored"),
    path("batchDeletion/<str:pk>", views.purgeBatch ,name="purgeBatch"),
    path("viewDeletion/<str:pk>", views.viewPurgeInfo ,name="viewPurge"),
    path("locationRegistration", views.registerLocation ,name="newLoc"),
    path("uploads/", views.consolidatedUpload, name='uploads'),

    path("csvMissingTicket/<str:pk>", views.downloadMissingTicket ,name="missingTicketDownload"),
    path("csvMissingSchedule/<str:pk>", views.downloadMissingSchedule ,name="missingScheduleDownload"),
    # MAIN PAGES
    #####
    # DATA HANDLERS
    path("yearRegistration/loading", views.registerYear, name='loadYear'),
    path("dataRegistration/loading", views.registerFootTraffic, name='loadData'),
    path("ticketRegistration/loading", views.registerTicketData, name='loadTicket'),
    path("closingRegistration/loading", views.registerClosingData, name='loadClosing'),
    # DATA HANDLERS  
    # VERIFICATION
]