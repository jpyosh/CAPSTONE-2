import datetime
import pandas
import holidays

phHolidays = holidays.PH()

def generateDays(input):

    if isinstance(input, int):
        chosenYear = int(input)
        startDate = datetime.date(chosenYear, 1, 1)

        dates = []
        yearWithinLoop = startDate.year
        dateWithinLoop = startDate

            # Generate dates for a selected year to be placed within an array that will be used to generate data
        while yearWithinLoop == chosenYear:
            dates.append(dateWithinLoop)
            dateWithinLoop += datetime.timedelta(days=1)
            yearWithinLoop = dateWithinLoop.year

            #Format dates into YYYY-MM-DD. Place within an array

        datesByDay = []
        for currentDate in dates:
            datesByDay.append(currentDate.strftime("%Y-%m-%d"))
                
            #Format dates into YYYY-MM. Place within an array

        datesByMonth = []
        for currentDate2 in dates:
            datesByMonth.append(currentDate2.strftime("%Y-%m"))
                
            #Format dates into YYYY. Place within an array
                
            datesByYear = []
        for currentDate3 in dates:
            datesByYear.append(currentDate3.strftime("%Y"))
                
                
            #Format dates into YYYY-WWW. Place within an array
                
            datesByWeek = []
        for currentDate4 in dates:
            iso = currentDate4.isocalendar()
            datesByWeek.append(f"{iso.year}" + "-" + f"{iso.week}")
                
                
        finalData = {
        "time_day": datesByDay,
        "time_week": datesByWeek,
        "time_month": datesByMonth,
        "time_year": datesByYear
        }

        df = pandas.DataFrame(finalData)

        df['time_day'] = pandas.to_datetime(df['time_day'])

            #create quarters
        df['time_quarter'] = df['time_day'].dt.to_period('Q').dt.strftime('Q%q-%Y')

        # generate holidays. To whoever that left it in the document, I hate you

        holidayArray = []
        for index, row in df.iterrows():
            holidayArray.append(phHolidays.get(row['time_day']))
        
        df['time_holiday'] = holidayArray
            #can now be placed within the database. dataframe is ready
        return df
    else:
        return