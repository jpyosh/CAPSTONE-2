import pandas, csv
import datetime
from django_pandas.io import read_frame
import numpy
from meteostat import Point, Daily

from django.shortcuts import render
from django.shortcuts import HttpResponse, redirect
from databaseHandler.functions.generateDays import generateDays
from databaseHandler.functions.dataCleaning import cleanFootTraffic, cleanTicketData, cleanClosingData
from django.contrib.auth.decorators import login_required

from django.http import FileResponse, JsonResponse

from .models import *

from django import forms
class LocationForm(forms.ModelForm):
    class Meta:
        model = Location_Dim
        fields = "__all__"


# Create your views here.

## LANDING PAGE
@login_required(login_url="/login")
def index(request):
    return render(request, 'databaseHandlerTemplates/handlerIndex.html')


## BETA YEAR GENERATION. COMBINE FUNCTIONS UPON INSERTION OF FOOTTRAFFIC DATA
def inputYear(request):
    return render(request, 'databaseHandlerTemplates/yearRegister.html')

def registerYear(request):

    chosenYear = int(request.POST['yearToRegister'])
    df = generateDays(chosenYear)
    df_html = df.to_html
    context = {'table': df_html}
    return render(request, 'databaseHandlerTemplates/displayGenerated_TEST.html', context)

@login_required(login_url="/login")
def registerLocation(request):
    if request.method == 'POST':
        form = LocationForm(request.POST or None)
        if form.is_valid():
            form.save()
    else:
        form = LocationForm()
    return render(request, 'databaseHandlerTemplates/registerNewLocation.html', {"form": form })


## FOOTTRAFFIC DATA INSERTION
@login_required(login_url="/login")
def inputFootTraffic(request):
    return render(request, 'databaseHandlerTemplates/trafficDataRegister.html')

@login_required(login_url="/login")
def registerFootTraffic(request):
    if request.method == 'POST':
        new_data = request.FILES['fileSelect']
        df = pandas.read_csv(new_data)

        availableLocations = read_frame(Location_Dim.objects.all())['location_name_abbreviated'].to_numpy()
        availableDates = read_frame(Time_Dim.objects.all())['time_day'].to_numpy()

        try: 
            metadata = cleanFootTraffic(df, availableLocations, availableDates)
        except: 
            context = {'table': pandas.DataFrame(columns=['TIME', 'FOREIGN', 'DOMESTIC', 'MALE', 'FEMALE', 'ORIGIN_UNCATEGORIZED', 'SEX_UNCATEGORIZED', 'UNCATEGORIZED', 'LOCATION']).to_html,
                    'totalInserted': 0,
                    'total': -1,
                    }
            return render(request, 'databaseHandlerTemplates/displayGenerated_TEST.html', context)
        else:
            if metadata == -1:
                context = {'table': pandas.DataFrame(columns=['TIME', 'FOREIGN', 'DOMESTIC', 'MALE', 'FEMALE', 'ORIGIN_UNCATEGORIZED', 'SEX_UNCATEGORIZED', 'UNCATEGORIZED', 'LOCATION']).to_html,
                    'totalInserted': 0,
                    'total': -1,
                    }
                return render(request, 'databaseHandlerTemplates/displayGenerated_TEST.html', context)

        cleanedData = pandas.DataFrame(metadata["cleanedData"])

        newBatch = batch.objects.create(
            batchtype = 'FT',
            file = new_data,
            user = request.user
        )

        cleanedData['TIME'] = pandas.to_datetime(df['TIME'])

        yearsFound = cleanedData['TIME'].dt.year.unique()
        print(yearsFound)

        for year in yearsFound:
            dateDf = pandas.DataFrame(generateDays(int(year)))
            for index, row in dateDf.iterrows():
                create = Time_Dim.objects.update_or_create(
                    time_year = row['time_year'],
                    time_month = row['time_month'],
                    time_week = row['time_week'],
                    time_day = row['time_day'],
                    time_quarter = row['time_quarter'],
                    time_holiday = row['time_holiday'],
                )

        #Find all daily data for all years detected in the submitted Data
        philippineWeather = Point(14.5833,120.9833, 16)
        weatherFindStart = datetime.datetime(yearsFound.min(), 1, 1)
        weatherFindEnd = datetime.datetime(yearsFound.max(), 12, 31)
        foundWeather = Daily(philippineWeather, weatherFindStart, weatherFindEnd)
        foundWeather = pandas.DataFrame(foundWeather.fetch())
        foundWeather = foundWeather.fillna(0)


        for index, row in cleanedData.iterrows():
            chosenWeatherRow = foundWeather.loc[row['TIME']]
            fetchedLocation = Location_Dim.objects.get(location_name_abbreviated=row['LOCATION'])
            fetchedDay = Time_Dim.objects.get(time_day=row['TIME'])

            findExisting = Weather_Dim.objects.filter(weather_time = fetchedDay)
            #Weather_Dim.objects.filter(weather_time = fetchedDay).delete() #ONLY ACTIVATE WHEN CHANGING VALUES BELOW
            if findExisting.exists(): 
                Weather_Dim.objects.filter(weather_time = fetchedDay).update(
                weather_rainValue = chosenWeatherRow['prcp'],
                weather_temperatureValue = chosenWeatherRow['tavg'],
                weather_windValue = chosenWeatherRow['wspd']
            )
            else:
                createWeather = Weather_Dim.objects.update_or_create(
                    weather_time = fetchedDay,
                    weather_rainValue = chosenWeatherRow['prcp'],
                    weather_temperatureValue = chosenWeatherRow['tavg'],
                    weather_windValue = chosenWeatherRow['wspd']
                )
            
        ##They need to be in their own loops because the Weather_Dim is fat and greedy and refuses to make FootTraffic_Fact do stuff
        for index, row in cleanedData.iterrows():
            fetchedLocation = Location_Dim.objects.get(location_name_abbreviated=row['LOCATION'])
            fetchedDay = Time_Dim.objects.get(time_day=row['TIME'])
            fetchedWeather = Weather_Dim.objects.get(weather_time=fetchedDay)
            chosenDataRow=cleanedData[(cleanedData['TIME']==row['TIME']) & (cleanedData['LOCATION']==row['LOCATION'])].iloc[0]
            FootTraffic_Fact.objects.filter(fact_time = fetchedDay, fact_location = fetchedLocation).delete()
            obj = FootTraffic_Fact.objects.create(
                fact_time = fetchedDay,
                fact_location = fetchedLocation,
                fact_weather = fetchedWeather,
                fact_foreign = chosenDataRow['FOREIGN'],
                fact_domestic = chosenDataRow['DOMESTIC'],
                fact_male = chosenDataRow['MALE'],
                fact_female = chosenDataRow['FEMALE'],
                fact_originUnknown = chosenDataRow['ORIGIN_UNCATEGORIZED'],
                fact_sexUnknown = chosenDataRow['SEX_UNCATEGORIZED'],
                fact_uncategorized = chosenDataRow['UNCATEGORIZED']
            )
            newConn = foottraffic_batch_bridge.objects.update_or_create(
                batchRef = newBatch,
                dataRef = obj
            )
        detectOverwrite(request)
        context = {'table': cleanedData.to_html,
                   'totalInserted': metadata['cleanedRows'],
                   'total': metadata['originalRows'],
                   }
    else:
        context = {'table': "ERROR: WRONG VALUES"}
    return render(request, 'databaseHandlerTemplates/displayGenerated_TEST.html', context)

## TICKET DATA INSERTION
@login_required(login_url="/login")
def inputTicketData(request):
    return render(request, 'databaseHandlerTemplates/ticketDataRegister.html')

@login_required(login_url="/login")
def registerTicketData(request):
    if request.method == 'POST':
        new_data = request.FILES['ticketSelect']
        df = pandas.read_csv(new_data)

        availableLocations = read_frame(Location_Dim.objects.all())['location_name_abbreviated'].to_numpy()
        availableDates = read_frame(Time_Dim.objects.all())['time_day'].to_numpy()

        try: 
            metadata = cleanTicketData(df, availableLocations, availableDates)
        except: 
            context = {'table': pandas.DataFrame(columns=['START_DATE', 'END_DATE', 'LOCATION', 'PRICE_NORMAL', 'PRICE_DISCOUNT']).to_html,
                    'totalInserted': 0,
                    'total': -1,
                    }
            return render(request, 'databaseHandlerTemplates/displayGenerated_TEST.html', context)
        else:
            if metadata == -1:
                context = {'table': pandas.DataFrame(columns=['START_DATE', 'END_DATE', 'LOCATION', 'PRICE_NORMAL', 'PRICE_DISCOUNT']).to_html,
                    'totalInserted': 0,
                    'total': -1,
                    }
                return render(request, 'databaseHandlerTemplates/displayGenerated_TEST.html', context)
            
        cleanedData = pandas.DataFrame(metadata["cleanedData"])
        context = {'table': cleanedData.to_html, 
                   'totalInserted': metadata['cleanedRows'],
                   'total': metadata['originalRows'],}

        newBatch = batch.objects.create(
            batchtype = 'TK',
            file = new_data,
            user = request.user
        )

        # INSERT TICKET DATA

        for index, row in cleanedData.iterrows():
            foundMatches = Time_Dim.objects.filter(time_day__range=[row['START_DATE'], row['END_DATE']])
            fetchedLocation = Location_Dim.objects.get(location_name_abbreviated=row['LOCATION'])
            for dateMatch in foundMatches:
                Ticket_Dim.objects.filter(ticket_date=dateMatch, ticket_location=fetchedLocation).delete()
                obj, created = Ticket_Dim.objects.update_or_create(
                    ticket_date = dateMatch,
                    ticket_location = fetchedLocation,
                    ticket_price_base = row['PRICE_NORMAL'],
                    ticket_price_discounted = row['PRICE_DISCOUNT']
                )
                newConn = ticket_batch_bridge.objects.update_or_create(
                    batchRef = newBatch,
                    dataRef = obj
                )
        detectOverwrite(request)
    else:
        context = {'table': "ERROR: WRONG VALUES"}
    return render(request, 'databaseHandlerTemplates/displayGenerated_TEST.html', context)

## CLOSING INFO DATA INSERTION
@login_required(login_url="/login")
def inputClosingData(request):
    return render(request, 'databaseHandlerTemplates/closingDataRegister.html')

@login_required(login_url="/login")
def registerClosingData(request):
    if request.method == 'POST':
        new_data = request.FILES['closingSelect']
        df = pandas.read_csv(new_data)

        availableLocations = read_frame(Location_Dim.objects.all())['location_name_abbreviated'].to_numpy()
        availableDates = read_frame(Time_Dim.objects.all())['time_day'].to_numpy()

        try: 
            metadata = cleanClosingData(df, availableLocations, availableDates)
        except: 
            context = {'table': pandas.DataFrame(columns=['LOCATION', 'START_DATE','END_DATE',
                        'MON_OPEN','MON_CLOSE','TUE_OPEN','TUE_CLOSE','WED_OPEN','WED_CLOSE','THURS_OPEN',
                        'THURS_CLOSE','FRI_OPEN','FRI_CLOSE','SAT_OPEN','SAT_CLOSE','SUN_OPEN','SUN_CLOSE']).to_html,
                    'totalInserted': 0,
                    'total': -1,
                    }
            return render(request, 'databaseHandlerTemplates/displayGenerated_TEST.html', context)
        else:
            if metadata == -1:
                context = {'table': pandas.DataFrame(columns=['LOCATION', 'START_DATE','END_DATE',
                        'MON_OPEN','MON_CLOSE','TUE_OPEN','TUE_CLOSE','WED_OPEN','WED_CLOSE','THURS_OPEN',
                        'THURS_CLOSE','FRI_OPEN','FRI_CLOSE','SAT_OPEN','SAT_CLOSE','SUN_OPEN','SUN_CLOSE']).to_html,
                    'totalInserted': 0,
                    'total': -1,
                    }
                return render(request, 'databaseHandlerTemplates/displayGenerated_TEST.html', context)

        cleanedData = metadata["cleanedData"]

        newBatch = batch.objects.create(
            batchtype = 'SH',
            file = new_data,
            user = request.user
        )

        for index, row in cleanedData.iterrows():
            foundMatches = Time_Dim.objects.filter(time_day__range=[row['START_DATE'], row['END_DATE']])
            fetchedLocation = Location_Dim.objects.get(location_name_abbreviated=row['LOCATION'])
            for dateMatch in foundMatches:
                selectedOpening = None
                selectedClosing = None

                fetchedWeekday = dateMatch.time_day.weekday()
                if fetchedWeekday == 0:
                    selectedOpening = row['MON_OPEN']
                    selectedClosing = row['MON_CLOSE']
                elif fetchedWeekday == 1:
                    selectedOpening = row['TUE_OPEN']
                    selectedClosing = row['TUE_CLOSE']
                elif fetchedWeekday == 2:
                    selectedOpening = row['WED_OPEN']
                    selectedClosing = row['WED_CLOSE']
                elif fetchedWeekday == 3:
                    selectedOpening = row['THURS_OPEN']
                    selectedClosing = row['THURS_CLOSE']
                elif fetchedWeekday == 4:
                    selectedOpening = row['FRI_OPEN']
                    selectedClosing = row['FRI_CLOSE']
                elif fetchedWeekday == 5:
                    selectedOpening = row['SAT_OPEN']
                    selectedClosing = row['SAT_CLOSE']
                else:
                    selectedOpening = row['SUN_OPEN']
                    selectedClosing = row['SUN_CLOSE']

                Schedule_Dim.objects.filter(schedule_date=dateMatch, schedule_location=fetchedLocation).delete()
                obj, created = Schedule_Dim.objects.update_or_create(
                    schedule_date = dateMatch,
                    schedule_location = fetchedLocation,
                    schedule_openingtime = selectedOpening,
                    schedule_closingtime = selectedClosing
                )
                newConn = sched_batch_bridge.objects.update_or_create(
                    batchRef = newBatch,
                    dataRef = obj
                )
                
        detectOverwrite(request)
        context = {'table': cleanedData.to_html, 'totalInserted': metadata['cleanedRows'],
                   'total': metadata['originalRows'],}
    else:
        context = {'table': "ERROR: WRONG VALUES"}
    return render(request, 'databaseHandlerTemplates/displayGenerated_TEST.html',context)

@login_required(login_url="/login")
def viewMissingDates(request):
    availableLocations = Location_Dim.objects.all()

    locationAndMissingDates = []
    for location in availableLocations:
        availableDates = FootTraffic_Fact.objects.filter(fact_location = location).values_list('fact_time')
        missingDates = Time_Dim.objects.exclude(id__in = availableDates)
        missingDates = read_frame(missingDates)
        missingDatesTotalled = missingDates.shape[0]
        locationAndMissingDates.append({'name': location.location_name_abbreviated, 'query': location, 'totalMissing': missingDatesTotalled})

    batches = batch.objects.all()

    batchesandMeta = []
    for row in batches:
        if row.batchtype == 'FT':
            total = foottraffic_batch_bridge.objects.filter(batchRef=row).count()
        elif row.batchtype == 'TK':
            total = ticket_batch_bridge.objects.filter(batchRef=row).count()
        elif row.batchtype == 'SH':
            total = sched_batch_bridge.objects.filter(batchRef=row).count()

        if total == 0:
            batchesandMeta.append({ "id": row.id, "presence": "inactive", "uploader": row.user.username, "type": row.get_batchtype_display(), "time": row.uploadtime})
        else:
            batchesandMeta.append({ "id": row.id, "presence": "active", "uploader": row.user.username,  "type": row.get_batchtype_display(), "time": row.uploadtime})

    return render(request, 'databaseHandlerTemplates/missingDatesPerLocation.html', {'missing': locationAndMissingDates, 'batches': batchesandMeta})

@login_required(login_url="/login")
def viewDatesForLocation(request, pk):
    availableLocations = Location_Dim.objects.get(pk = pk)
    availableDates = FootTraffic_Fact.objects.filter(fact_location = availableLocations).values_list('fact_time')
    missingDates = Time_Dim.objects.exclude(id__in = availableDates).order_by('time_day')
    missingDates = read_frame(missingDates)[['time_month','time_day','time_year']]
    missingDatesTotalled = missingDates[['time_month','time_day']].groupby('time_month').count()

    missingDatesGroupedWithMonths = []
    for index, row in missingDatesTotalled.iterrows():
        matching_rows = missingDates[missingDates['time_month'] == index]
        year = matching_rows['time_year'].iloc[0] if not matching_rows.empty else ''
        # Extract month number from '2025-01' format
        month_num = int(index.split('-')[1]) if isinstance(index, str) and '-' in index else index
        matching_rows = matching_rows['time_day'].to_list()
        missingDatesGroupedWithMonths.append({'month': month_num, 'matching': matching_rows, 'year': year})

    context = {'name' : availableLocations.location_name_abbreviated,
               'trafficmissing' : missingDatesGroupedWithMonths}
    
    availableDates = Ticket_Dim.objects.filter(ticket_location = availableLocations).values_list('ticket_date')
    missingDates = Time_Dim.objects.exclude(id__in = availableDates).order_by('time_day')
    missingDates = read_frame(missingDates)[['time_month','time_day','time_year']]
    missingDatesTotalled = missingDates[['time_month','time_day']].groupby('time_month').count()

    missingDatesGroupedWithMonths = []
    for index, row in missingDatesTotalled.iterrows():
        matching_rows = missingDates[missingDates['time_month'] == index]
        year = matching_rows['time_year'].iloc[0] if not matching_rows.empty else ''
        # Extract month number from '2025-01' format
        month_num = int(index.split('-')[1]) if isinstance(index, str) and '-' in index else index
        matching_rows = matching_rows['time_day'].to_list()
        missingDatesGroupedWithMonths.append({'month': month_num, 'matching': matching_rows, 'year': year})

    context.update({'ticketmissing': missingDatesGroupedWithMonths})

    availableDates = Schedule_Dim.objects.filter(schedule_location = availableLocations).values_list('schedule_date')
    missingDates = Time_Dim.objects.exclude(id__in = availableDates).order_by('time_day')
    missingDates = read_frame(missingDates)[['time_month','time_day','time_year']]
    missingDatesTotalled = missingDates[['time_month','time_day']].groupby('time_month').count()

    missingDatesGroupedWithMonths = []
    for index, row in missingDatesTotalled.iterrows():
        matching_rows = missingDates[missingDates['time_month'] == index]
        year = matching_rows['time_year'].iloc[0] if not matching_rows.empty else ''
        # Extract month number from '2025-01' format
        month_num = int(index.split('-')[1]) if isinstance(index, str) and '-' in index else index
        matching_rows = matching_rows['time_day'].to_list()
        missingDatesGroupedWithMonths.append({'month': month_num, 'matching': matching_rows, 'year': year})

    context.update({'schedmissing': missingDatesGroupedWithMonths})
    return render(request, 'databaseHandlerTemplates/locationSpecificMissing.html', context)

@login_required(login_url="/login")
def downloadMissingTraffic(request, pk):
    availableLocations = Location_Dim.objects.get(location_name_abbreviated = pk)
    availableDates = FootTraffic_Fact.objects.filter(fact_location = availableLocations).values_list('fact_time')
    missingDates = Time_Dim.objects.exclude(id__in = availableDates).exclude(time_day__gte = datetime.date.today()).order_by('time_day')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="missingfoottraffic.csv"'
    

    writer = csv.writer(response)
    writer.writerow(['TIME', 'FOREIGN', 'DOMESTIC', 'MALE', 'FEMALE', 'ORIGIN_UNCATEGORIZED', 'SEX_UNCATEGORIZED', 'UNCATEGORIZED', 'LOCATION'])

    for row in missingDates:
        writer.writerow([(row.time_day).strftime("%d/%m/%Y"), None, None, None, None, None, None, None, pk])
    return response

@login_required(login_url="/login")
def downloadMissingTicket(request, pk):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="missingticket.csv"'

    writer = csv.writer(response)
    writer.writerow(['START_DATE', 'END_DATE', 'LOCATION', 'PRICE_NORMAL', 'PRICE_DISCOUNT'])
    writer.writerow([None, None, pk, 0, 0])
    return response

def downloadMissingSchedule(request, pk):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="missingschedule.csv"'

    writer = csv.writer(response)
    writer.writerow(['LOCATION', 'START_DATE','END_DATE',
                        'MON_OPEN','MON_CLOSE','TUE_OPEN','TUE_CLOSE','WED_OPEN','WED_CLOSE','THURS_OPEN',
                        'THURS_CLOSE','FRI_OPEN','FRI_CLOSE','SAT_OPEN','SAT_CLOSE','SUN_OPEN','SUN_CLOSE'])
    writer.writerow([pk, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None])
    return response

@login_required(login_url="/login")
def downloadSelectedCSV(request, pk):
    object = batch.objects.get(pk=pk)

    return FileResponse(
        object.file.open(),
        as_attachment=True,
        filename=object.file.name
    )

@login_required(login_url="/login")
def consolidatedUpload(request):
    batches = batch.objects.all()

    batchesandMeta = []
    for row in batches:
        if row.batchtype == 'FT':
            total = foottraffic_batch_bridge.objects.filter(batchRef=row).count()
        elif row.batchtype == 'TK':
            total = ticket_batch_bridge.objects.filter(batchRef=row).count()
        elif row.batchtype == 'SH':
            total = sched_batch_bridge.objects.filter(batchRef=row).count()

        if total == 0:
            batchesandMeta.append({ "id": row.id, "presence": "inactive", "uploader": row.user.username, "type": row.get_batchtype_display(), "time": row.uploadtime})
        else:
            batchesandMeta.append({ "id": row.id, "presence": "active", "uploader": row.user.username,  "type": row.get_batchtype_display(), "time": row.uploadtime})


    availableLocations = Location_Dim.objects.all()

    locationAndMissingDates = []
    for location in availableLocations:
        availableDates = FootTraffic_Fact.objects.filter(fact_location = location).values_list('fact_time')
        missingDates = Time_Dim.objects.exclude(id__in = availableDates)
        missingDates = read_frame(missingDates)
        missingDatesTotalled = missingDates.shape[0]
        locationAndMissingDates.append({'name': location.location_name_abbreviated, 'query': location, 'totalMissing': missingDatesTotalled})
    
    if request.method == 'POST':
        form = LocationForm(request.POST or None)
        if form.is_valid():
            form.save()
    else:
        form = LocationForm()
    
    return render(request, 'databaseHandlerTemplates/consolidatedUpload.html', {'missing': locationAndMissingDates, 'batches': batchesandMeta, 'form': form})

@login_required(login_url="/login")
def purgeBatch(request, pk): 
    object = batch.objects.get(pk=pk)
    if object.batchtype == 'FT':
        value = foottraffic_batch_bridge.objects.filter(batchRef=object).values_list('dataRef', flat=True)
        value = FootTraffic_Fact.objects.filter(pk__in=value).delete()
    elif object.batchtype == 'TK':
        value = ticket_batch_bridge.objects.filter(batchRef=object).values_list('dataRef',  flat=True)
        value = Ticket_Dim.objects.filter(pk__in=value).delete()
    elif object.batchtype == 'SH':
        value = sched_batch_bridge.objects.filter(batchRef=object).values_list('dataRef',  flat=True)
        value = Schedule_Dim.objects.filter(pk__in=value).delete()

    deletionInfo.objects.create(
        batchname  = object,
        user = request.user
    )

    return redirect('missingDates')

@login_required(login_url="/login")
def viewPurgeInfo(request, pk):
    try:
        selectedBatch = batch.objects.get(pk=pk)
        deletionRecord = deletionInfo.objects.filter(batchname=selectedBatch).first()
        
        if not deletionRecord:
            return JsonResponse({
                'success': False,
                'error': 'Deletion information not found for this batch.'
            })
        
        return JsonResponse({
            'success': True,
            'batch_id': selectedBatch.pk,
            'batch_type': selectedBatch.get_batchtype_display(),
            'deleted_by': deletionRecord.user.username,
            'deletion_time': deletionRecord.deletionTime.strftime('%B %d, %Y at %I:%M %p') if deletionRecord.deletionTime else 'Unknown'
        })
    except batch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Batch not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        })

def detectOverwrite(request):

    inactiveBatches = batch.objects.exclude(pk__in=ticket_batch_bridge.objects.all().values_list('batchRef')).exclude(pk__in=foottraffic_batch_bridge.objects.all().values_list('batchRef')).exclude(pk__in=sched_batch_bridge.objects.all().values_list('batchRef')).exclude(pk__in=deletionInfo.objects.all().values_list('batchname'))
    
    for row in inactiveBatches:
        deletionInfo.objects.create(
        batchname  = row,
        user = request.user
        )