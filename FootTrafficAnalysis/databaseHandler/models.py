from django.db import models
from django.conf import settings

# Create your models here.
class Time_Dim(models.Model):
    time_year = models.TextField(max_length=5)
    time_quarter = models.TextField(max_length=255)
    time_month = models.TextField(max_length=255)
    time_week = models.TextField(max_length=255)
    time_day = models.DateField()
    time_holiday = models.TextField(max_length=255, null=True)

    def __str__(self):
        return str(self.time_day)
    
class Location_Dim(models.Model):
    location_name_abbreviated = models.TextField(max_length=255, unique=True)
    location_name_full = models.TextField(max_length=255)
    location_latitude = models.DecimalField(decimal_places=7, max_digits=255)
    location_longitude = models.DecimalField(decimal_places=7, max_digits=255)

    def __str__(self):
        return str(self.location_name_abbreviated)
    
class Ticket_Dim(models.Model):
    ticket_date = models.ForeignKey(Time_Dim, on_delete=models.CASCADE)
    ticket_location = models.ForeignKey(Location_Dim, on_delete=models.CASCADE)
    ticket_price_base = models.DecimalField(decimal_places=2, max_digits=10)
    ticket_price_discounted = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return str(self.ticket_date) + ' ' + str(self.ticket_location)
    
class Schedule_Dim(models.Model):
    schedule_date = models.ForeignKey(Time_Dim, on_delete=models.CASCADE)
    schedule_location = models.ForeignKey(Location_Dim, on_delete=models.CASCADE)
    schedule_openingtime = models.TimeField(null=True)
    schedule_closingtime = models.TimeField(null=True)

    def __str__(self):
        return str(self.schedule_date) + ' ' + str(self.schedule_location)
    
#REMOVE CLOUD VALUE. 
    
class Weather_Dim(models.Model):
    weather_time = models.ForeignKey(Time_Dim, on_delete=models.CASCADE,null=True)
    weather_rainValue = models.DecimalField(decimal_places=2, max_digits=10)
    weather_temperatureValue = models.DecimalField(decimal_places=2, max_digits=10)
    weather_windValue = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return str(self.weather_time) +','+ str(self.weather_rainValue) +','+ str(self.weather_temperatureValue) +','+ str(self.weather_windValue)

class FootTraffic_Fact(models.Model):
    fact_time = models.ForeignKey(Time_Dim, on_delete=models.CASCADE)
    fact_location = models.ForeignKey(Location_Dim, on_delete=models.CASCADE)
    fact_weather = models.ForeignKey(Weather_Dim, on_delete=models.CASCADE)
    fact_foreign = models.IntegerField()
    fact_domestic = models.IntegerField()
    fact_male = models.IntegerField()
    fact_female = models.IntegerField()
    fact_originUnknown = models.IntegerField()
    fact_sexUnknown = models.IntegerField()
    fact_uncategorized = models.IntegerField()

    def __str__(self):
        return 'FT'+ str(self.fact_time) +'_'+ str(self.fact_location)
    
class batch(models.Model):
    BATCHTYPECHOICES = [
    ("TK", "Ticket"),
    ("FT", "Foot Traffic"),
    ("SH", "Schedule"),
    ]
    batchtype = models.CharField(max_length=2, choices=BATCHTYPECHOICES)
    file = models.FileField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploadtime = models.DateTimeField(auto_now_add=True, null=True)
    def __str__(self):
        return str(self.pk) +'_'+ str(self.batchtype)

class ticket_batch_bridge(models.Model):
    batchRef = models.ForeignKey(batch, on_delete=models.CASCADE)
    dataRef = models.ForeignKey(Ticket_Dim, on_delete=models.CASCADE)
    def __str__(self):
        return str(self.batchRef) +'_'+ str(self.dataRef)

class sched_batch_bridge(models.Model):
    batchRef = models.ForeignKey(batch, on_delete=models.CASCADE)
    dataRef = models.ForeignKey(Schedule_Dim, on_delete=models.CASCADE)
    def __str__(self):
        return str(self.batchRef) +'_'+ str(self.dataRef)

class foottraffic_batch_bridge(models.Model):
    batchRef = models.ForeignKey(batch, on_delete=models.CASCADE)
    dataRef = models.ForeignKey(FootTraffic_Fact, on_delete=models.CASCADE)
    def __str__(self):
        return str(self.batchRef) +'_'+ str(self.dataRef)
    
class deletionInfo(models.Model):
    batchname  = models.ForeignKey(batch, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    deletionTime = models.DateTimeField(auto_now_add=True, null=True)
