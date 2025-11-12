from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Time_Dim)
admin.site.register(Location_Dim)
admin.site.register(Ticket_Dim)
admin.site.register(Schedule_Dim)
admin.site.register(Weather_Dim)
admin.site.register(FootTraffic_Fact)





