from django.shortcuts import render 
from django.shortcuts import HttpResponse
from django.apps import apps
from django_pandas.io import read_frame
import pandas
from django.core.cache import cache
import datetime, csv
from geopy import distance
from datetime import date, timedelta

from dataAnalytics.functions.graphingDescriptive import *
from dataAnalytics.functions.FormattedARIMAFunct import *
from dataAnalytics.functions.kmeansTest import *
from django.contrib.auth.decorators import login_required

from .models import *


# Create your views here.
@login_required(login_url="/login")
def index(request):
    Dates = apps.get_model('databaseHandler', 'time_dim')
    years = read_frame(Dates.objects.all())['time_year']
    years = years.unique()
    context = {'years': years}
    return render(request, 'dataAnalyticsTemplates/index.html', context)

@login_required(login_url="/login")
def cacheData(request):

    chosenYear = int(request.POST.get('chosenYear'))

    FootTraffic = apps.get_model('databaseHandler', 'foottraffic_fact')
    data = read_frame(FootTraffic.objects.all().select_related())
    splitWeather = data['fact_weather'].str.split(",",expand=True)

    data['rain'] = splitWeather[1]
    data['temp'] = splitWeather[2]
    data['wind'] = splitWeather[3]

    data = data.rename(columns={"fact_time": "date", "fact_location": "location", 
                         "fact_foreign": "foreign", "fact_domestic": "domestic",
                         "fact_male": "male", "fact_female": "female",
                         "fact_originUnknown": "originUnknown", "fact_sexUnknown": "sexUnknown",
                         "fact_uncategorized": "uncategorized"
                         })
    
    data = data.drop(['id', 'fact_weather'], axis=1)

    Tickets = apps.get_model('databaseHandler', 'ticket_dim')
    ticketData = read_frame(Tickets.objects.all())

    ticketData = ticketData.rename(columns={"ticket_location": "location", "ticket_date": "date"})
    data = pandas.merge(data, ticketData, how='inner', on=['location', 'date'])

    Schedule = apps.get_model('databaseHandler', 'schedule_dim')
    scheduleData = read_frame(Schedule.objects.all())

    scheduleData = scheduleData.rename(columns={"schedule_location": "location", "schedule_date": "date"})
    data = pandas.merge(data, scheduleData, how='inner', on=['location', 'date'])

    Dates = apps.get_model('databaseHandler', 'time_dim')
    timeData = read_frame(Dates.objects.all())

    timeData = timeData.rename(columns={"time_day": "date"})
    timeData['date']=pandas.to_datetime(timeData['date'])
    data['date']=pandas.to_datetime(data['date'])
    data = pandas.merge(data, timeData, how='left', on='date')

    data['time_year']=pandas.to_numeric(data['time_year'], downcast='integer', errors='coerce')

    data = data.drop(['id_x', 'id_y', 'id'], axis=1)

    data = data.rename(columns={"ticket_price_base" : "baseTicket", "ticket_price_discounted" : "discountTicket",
                                "schedule_openingtime" : "openingTime", "schedule_closingtime" : "closingTime"
                         })
    
    data = data[data.time_year >= chosenYear]

    TicketClustering.objects.all().delete()
    DurationClustering.objects.all().delete()
    config = date.min

    for key, value in data.iterrows():
        create = TicketClustering.objects.create(
            price = value['baseTicket'],
            value = value['domestic'] + value['foreign'] + value['originUnknown'] + value['uncategorized'],
            location = value['location'],
            year = value['time_year']
        )

        diff = 0
        if value['openingTime'] == None or value['closingTime'] == None:
            diff = 0
        elif value['openingTime'] == value['closingTime']:
            diff = 24
        else:
            if value['closingTime'] < value['openingTime']:
                bruh = datetime.datetime.combine(config+timedelta(days=1), value['closingTime']) - datetime.datetime.combine(config, value['openingTime'])
                hour = bruh.total_seconds()/3600
                diff = hour
            else:
                bruh = datetime.datetime.combine(config, value['closingTime']) - datetime.datetime.combine(config, value['openingTime'])
                hour = bruh.total_seconds()/3600
                diff = hour
        create = DurationClustering.objects.create(
            duration = diff,
            value = value['domestic'] + value['foreign'] + value['originUnknown'] + value['uncategorized'],
            location = value['location'],
            year = value['time_year']
        )
    
    arimaPredictions = arimaPredictAll(data)
    #Arima predictions must always reset the entire table
    totalPassed = 0
    ArimaPredictions.objects.all().delete() 
    PredictionPower.objects.all().delete()
    for value in arimaPredictions:
        toInsert = value.get('dataframe')
        totalPassed = totalPassed + value.get('meetsStandard')
        create = PredictionPower.objects.create(
                model = value.get('location'),
                value= value.get('detailedVal'),
            )
        for key, value in toInsert.iterrows():
            create = ArimaPredictions.objects.update_or_create(
                day = key,
                location = value['location'],
                value = value['value'],
                valueType = value['valueType'],
            )
    if totalPassed!=0:
        totalPassed = totalPassed/len(arimaPredictions)
    else: 
        totalPassed = 0
    
    #ADD LOCATION HERE IT WONT WORK IF YOU DONT
    Location = apps.get_model('databaseHandler', 'location_dim')
    locationData = read_frame(Location.objects.all())
    trendAnalysis = pandas.DataFrame(arimaPredictions)[['pos', 'neg', 'location', 'relativePref']] #Configure how you want
    trendAnalysis.dropna(inplace=True)

    locations =  data['location'].unique()
    locationMatrix = pandas.DataFrame(index=locations, columns=locations)

    for location1 in locations:
        for location2 in locations:
            coords1 = locationData.loc[locationData['location_name_abbreviated'] == location1, ['location_latitude', 'location_longitude']].iloc[0]
            coords2 = locationData.loc[locationData['location_name_abbreviated'] == location2, ['location_latitude', 'location_longitude']].iloc[0]
            coords1 = (coords1['location_latitude'], coords1['location_longitude'])
            coords2 = (coords2['location_latitude'], coords2['location_longitude'])
            distanceCalc = distance.distance(coords1, coords2).km
            locationMatrix.loc[location1, location2] = distanceCalc

    positiveTrend = trendAnalysis[trendAnalysis.relativePref >= 0.10]['location']
    negativeTrend = trendAnalysis[trendAnalysis.relativePref <= -0.10]['location']

    ArimaInsights.objects.all().delete()

    #if not positiveTrend.empty:
    #    ArimaInsights.objects.create(
    #        location = 'General',
    #        text = ('These locations appear to have an incoming rise in activity: ' + ', '.join(positiveTrend))
    #    )

    #if not negativeTrend.empty:
    #    ArimaInsights.objects.create(
    #        location = 'General',
    #        text = ('These locations appear to have an incoming decrease in activity: ' + ', '.join(negativeTrend))
    #    )

    for location in locations:
        nearbyLoc = locationMatrix.loc[locationMatrix[location] <= 0.255].index
        fullName = locationData.loc[locationData['location_name_abbreviated'] == location, ['location_name_full']].iloc[0]['location_name_full']

        messages = []

        if positiveTrend.isin([location]).any():
            messages.append('1. '+ fullName + " may be experiencing a notable positive boost in foot traffic.")
            messages.append("2. It may be advisable to continue with promoting the site and to allocate security to manage the crowds.")
            if negativeTrend.isin(nearbyLoc).any():
                negNear = set(nearbyLoc).intersection(negativeTrend)
                trueNames = []
                for i in negNear:
                    trueNames.append(locationData.loc[locationData['location_name_abbreviated'] == i, ['location_name_full']].iloc[0]['location_name_full'])
                messages.append('3. Nearby locations, ' + ', '.join(trueNames) + ' will be experiencing a fall in activity. ')
                messages.append('4. Consider promoting those sites in this area to prevent overcrowding')

        elif negativeTrend.isin([location]).any():
            messages.append('1. '+fullName + " may be experiencing a notable fall in foot traffic. Prioritize promoting this site in social media or holding an event in this location.")
            if nearbyLoc.empty:
                messages.append('Consider concentrating on social media promotion')
            elif positiveTrend.isin(nearbyLoc).any():
                posNearby = set(nearbyLoc).intersection(positiveTrend)
                trueNames = []
                for i in posNearby:
                    trueNames.append(locationData.loc[locationData['location_name_abbreviated'] == i, ['location_name_full']].iloc[0]['location_name_full'])
                messages.append('2. Nearby locations, ' + ', '.join(trueNames) + ' will be experiencing a positive boost. ')
                messages.append('3. Consider promoting the site in those areas to prevent overcrowding and to promote this site')
        else: 
            messages.append('1. No notable increase or decrease in foot traffic is foreseen. Keep up with promotions')

        for message in messages:
            ArimaInsights.objects.create(
            location = location,
            text = message
            )
    
    clusters = selectBestKmeans(data)

    OriginClustering.objects.all().delete()
    GenderClustering.objects.all().delete()
    ClusteringPower.objects.all().delete()

    origdf = clusters['origin_model']
    genddf = clusters['gender_model']

    for key, value in origdf.iterrows():
        create = OriginClustering.objects.create(
            foreign = value['foreign'],
            domestic = value['domestic'],
            location = value['location'],
            year = value['time_year'],
            cluster = value['clusters']
        )
    
    for key, value in genddf.iterrows():
        create = GenderClustering.objects.create(
            male = value['male'],
            female = value['female'],
            location = value['location'],
            year = value['time_year'],
            cluster = value['clusters']
        )

    create = ClusteringPower.objects.create(
            model = 'Origin',
            value = clusters['origin_res']
    )
    create = ClusteringPower.objects.create(
            model = 'Gender',
            value = clusters['gender_res']
    )

    logs = pandas.DataFrame(arimaPredictions)['logs'].to_list()
    
    flattenedLogs = []
    for i in logs:
        for j in i:
            flattenedLogs.append(j)

    print(logs)

    cache.set("footTrafficData", data)
    #context = {'graph1': data.to_html}
    # Replaced the finishNotice.html with the data-cube.html...
    return render(request, 'dataAnalyticsTemplates/data-cube.html', {'logs': flattenedLogs})
    #return render(request, 'dataAnalyticsTemplates/displayGenerated_TEST.html', context)

def viewDescriptive(request):
    return render(request, 'viewdata.html')

def downloadCubeCSV(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data_cube.csv"'
    data=pandas.DataFrame(cache.get('footTrafficData'))

    writer = csv.writer(response)
    writer.writerow(data.columns)

    for index, row in data.iterrows():
        writer.writerow([row['date'],row['location'],row['foreign'],row['domestic']
                         ,row['male'],row['female'],row['originUnknown'],row['sexUnknown'],
                         row['uncategorized'],row['rain'],row['temp'],row['wind'],row['baseTicket']
                         ,row['discountTicket'],row['openingTime'],row['closingTime'],row['time_year']
                         ,row['time_quarter'],row['time_month'],row['time_week'],row['time_holiday']])

    return response
