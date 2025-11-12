from django.db import models

# Create your models here.

class ArimaPredictions(models.Model):
    day = models.DateField()
    location = models.TextField(max_length=20)
    value = models.DecimalField(decimal_places=2, max_digits=255)
    valueType = models.TextField(max_length=20)

class PredictionPower(models.Model):
    model = models.TextField(max_length=20)
    value = models.DecimalField(decimal_places=2, max_digits=10)

class ArimaInsights(models.Model):
    text = models.TextField(max_length=1000)
    location = models.TextField(max_length=20)

class TicketClustering(models.Model):
    price = models.DecimalField(decimal_places=2, max_digits=10)
    value = models.IntegerField()
    location = models.TextField(max_length=20)
    year = models.TextField(max_length=5)

class DurationClustering(models.Model):
    duration = models.DecimalField(decimal_places=2, max_digits=10)
    value = models.IntegerField()
    location = models.TextField(max_length=20)
    year = models.TextField(max_length=5)

class GenderClustering(models.Model):
    female = models.DecimalField(decimal_places=2, max_digits=10)
    male = models.DecimalField(decimal_places=2, max_digits=10)
    location = models.TextField(max_length=20)
    year = models.TextField(max_length=5)
    cluster = models.TextField(max_length=20)

class OriginClustering(models.Model):
    foreign = models.DecimalField(decimal_places=2, max_digits=10)
    domestic = models.DecimalField(decimal_places=2, max_digits=10)
    location = models.TextField(max_length=20)
    year = models.TextField(max_length=5)
    cluster = models.TextField(max_length=20)

class ClusteringPower(models.Model):
    model = models.TextField(max_length=20)
    value = models.DecimalField(decimal_places=2, max_digits=10)