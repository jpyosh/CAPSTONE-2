import pandas 
import math

def cleanFootTraffic(new_data, availableLocations, availableDates):

    df=new_data
    availableDates = pandas.to_datetime(availableDates)

    referenceList = list(['TIME', 'FOREIGN', 'DOMESTIC', 'MALE', 'FEMALE', 'ORIGIN_UNCATEGORIZED', 'SEX_UNCATEGORIZED', 'UNCATEGORIZED', 'LOCATION'])
    print(df.columns)
    print(referenceList)
    if (list(df.columns) == referenceList):
        print("Headers match! Will proceed with cleaning")
        df['TIME']=pandas.to_datetime(df['TIME'], format='%d/%m/%Y')
        df['FOREIGN']=pandas.to_numeric(df['FOREIGN'])
        df['DOMESTIC']=pandas.to_numeric(df['DOMESTIC'])
        df['MALE']=pandas.to_numeric(df['MALE'])
        df['FEMALE']=pandas.to_numeric(df['FEMALE'])
        df['ORIGIN_UNCATEGORIZED']=pandas.to_numeric(df['ORIGIN_UNCATEGORIZED'])
        df['SEX_UNCATEGORIZED']=pandas.to_numeric(df['SEX_UNCATEGORIZED'])
        df['UNCATEGORIZED']=pandas.to_numeric(df['UNCATEGORIZED'])

        initialRows = len(df.index)
        blanksCount = df.shape[0] - df.dropna().shape[0]

        for key, value in df.iterrows(): #Preserve discrepancies to be fixed later
            if not math.isnan(value['FOREIGN']) or not math.isnan(value['DOMESTIC']) or not math.isnan(value['MALE']) or not math.isnan(value['FEMALE']):
                df.loc[key] = df.loc[key].fillna({"FOREIGN": 0, "DOMESTIC": 0, "MALE": 0, "FEMALE": 0, 'ORIGIN_UNCATEGORIZED':0, 'SEX_UNCATEGORIZED':0 })

        #df = df[pandas.to_datetime(df.TIME).isin(availableDates)]
        df = df[df.LOCATION.isin(availableLocations)]

        foreignMean = df['FOREIGN'].mean()
        if math.isnan(foreignMean):
            foreignMean = 0
        df.fillna({"FOREIGN": foreignMean}, inplace=True)
        df['FOREIGN'] = df['FOREIGN'].apply(lambda x: math.floor(x))

        domesticMean = df['DOMESTIC'].mean()
        if math.isnan(domesticMean):
            domesticMean = 0
        df.fillna({"DOMESTIC": domesticMean}, inplace=True)
        df['DOMESTIC'] = df['DOMESTIC'].apply(lambda x: math.floor(x))

        maleMean = df['MALE'].mean()
        if math.isnan(maleMean):
            maleMean = 0
        df.fillna({"MALE": maleMean}, inplace=True)
        df['MALE'] = df['MALE'].apply(lambda x: math.floor(x))

        femaleMean = df['FEMALE'].mean()
        if math.isnan(femaleMean):
            femaleMean = 0
        df.fillna({"FEMALE": femaleMean}, inplace=True)
        df['FEMALE'] = df['FEMALE'].apply(lambda x: math.floor(x))

        originUMean = df['ORIGIN_UNCATEGORIZED'].mean()
        if math.isnan(originUMean):
            originUMean = 0
        df.fillna({"ORIGIN_UNCATEGORIZED": originUMean}, inplace=True)
        df['ORIGIN_UNCATEGORIZED'] = df['ORIGIN_UNCATEGORIZED'].apply(lambda x: math.floor(x))

        sexUMean = df['SEX_UNCATEGORIZED'].mean()
        if math.isnan(sexUMean):
            sexUMean = 0
        df.fillna({"SEX_UNCATEGORIZED": sexUMean}, inplace=True)
        df['SEX_UNCATEGORIZED'] = df['SEX_UNCATEGORIZED'].apply(lambda x: math.floor(x))

        UMean = df['UNCATEGORIZED'].mean()
        if math.isnan(UMean):
            UMean = 0
        df.fillna({"UNCATEGORIZED": UMean}, inplace=True)
        df['UNCATEGORIZED'] = df['UNCATEGORIZED'].apply(lambda x: math.floor(x))

        df.dropna(subset=['TIME'], inplace = True)
        df.dropna(subset=['LOCATION'], inplace = True)

        for index, row in df.iterrows():
            discrepancy = row[['FOREIGN', 'DOMESTIC','ORIGIN_UNCATEGORIZED']].sum() - row[['MALE', 'FEMALE','SEX_UNCATEGORIZED']].sum()
            if discrepancy<0:
                df.at[index,'ORIGIN_UNCATEGORIZED'] = (discrepancy*-1) + row['ORIGIN_UNCATEGORIZED']
            elif discrepancy>0:
                df.at[index,'SEX_UNCATEGORIZED'] = (discrepancy*1) + row['SEX_UNCATEGORIZED']

        finalRows = len(df.index)

        metaData = {
            'cleanedData': df,
            'originalRows': initialRows,
            'cleanedRows': finalRows,
            'blanksFound': blanksCount
        }
        return metaData
    else:
        print("Incorrect columns! Do not proceed!")
        return -1
    
def cleanTicketData(newData, availableLocations, availableDates):
    df=newData
    referenceList = list(['START_DATE', 'END_DATE', 'LOCATION', 'PRICE_NORMAL', 'PRICE_DISCOUNT'])
    availableDates = pandas.to_datetime(availableDates)

    if (list(df.columns) == referenceList):
        print('Correct columns, will proceed')
        initialRows = len(df.index)
        blanksCount = df.shape[0] - df.dropna().shape[0]
    
        df['START_DATE']=pandas.to_datetime(df['START_DATE'], format='%d/%m/%Y')
        df['END_DATE']=pandas.to_datetime(df['END_DATE'], format='%d/%m/%Y')
        df['PRICE_NORMAL']=pandas.to_numeric(df['PRICE_NORMAL'])
        df['PRICE_DISCOUNT']=pandas.to_numeric(df['PRICE_DISCOUNT'])
        df.dropna(inplace = True)

        df = df[pandas.to_datetime(df.START_DATE).isin(availableDates)]
        df = df[pandas.to_datetime(df.END_DATE).isin(availableDates)]
        df = df[df.LOCATION.isin(availableLocations)]

        finalRows = len(df.index)

        metaData = {
            'cleanedData': df,
            'originalRows': initialRows,
            'cleanedRows': finalRows,
            'blanksFound': blanksCount
        }

        return metaData
    
    ## IF START DATE IS GONE, SIMPLY ADD THE DATE OF 
    ## THE END DATE OF THE LATEST ROW OF THAT CERTAIN LOCATION
    
    else:
        print('Aborted proceedure. Incorrect columns found')
        return -1

def cleanClosingData(newData, availableLocations, availableDates):
    df=newData
    availableDates = pandas.to_datetime(availableDates)
    referenceList = list(['LOCATION', 'START_DATE','END_DATE',
                        'MON_OPEN','MON_CLOSE','TUE_OPEN','TUE_CLOSE','WED_OPEN','WED_CLOSE','THURS_OPEN',
                        'THURS_CLOSE','FRI_OPEN','FRI_CLOSE','SAT_OPEN','SAT_CLOSE','SUN_OPEN','SUN_CLOSE'])

    if (list(df.columns) == referenceList):
        print('Correct columns, will proceed')
        initialRows = len(df.index)
        blanksCount = df.shape[0] - df.dropna().shape[0]
    
        df['START_DATE']=pandas.to_datetime(df['START_DATE'], format='%d/%m/%Y')
        df['END_DATE']=pandas.to_datetime(df['END_DATE'], format='%d/%m/%Y')

        df['MON_OPEN']=pandas.to_datetime(df['MON_OPEN'], format='%H:%M:%S').dt.time
        df['MON_CLOSE']=pandas.to_datetime(df['MON_CLOSE'], format='%H:%M:%S').dt.time

        df['TUE_OPEN']=pandas.to_datetime(df['TUE_OPEN'], format='%H:%M:%S').dt.time
        df['TUE_CLOSE']=pandas.to_datetime(df['TUE_CLOSE'], format='%H:%M:%S').dt.time

        df['WED_OPEN']=pandas.to_datetime(df['WED_OPEN'], format='%H:%M:%S').dt.time
        df['WED_CLOSE']=pandas.to_datetime(df['WED_CLOSE'], format='%H:%M:%S').dt.time

        df['THURS_OPEN']=pandas.to_datetime(df['THURS_OPEN'], format='%H:%M:%S').dt.time
        df['THURS_CLOSE']=pandas.to_datetime(df['THURS_CLOSE'], format='%H:%M:%S').dt.time

        df['FRI_OPEN']=pandas.to_datetime(df['FRI_OPEN'], format='%H:%M:%S').dt.time
        df['FRI_CLOSE']=pandas.to_datetime(df['FRI_CLOSE'], format='%H:%M:%S').dt.time

        df['SAT_OPEN']=pandas.to_datetime(df['SAT_OPEN'], format='%H:%M:%S').dt.time
        df['SAT_CLOSE']=pandas.to_datetime(df['SAT_CLOSE'], format='%H:%M:%S').dt.time

        df['SUN_OPEN']=pandas.to_datetime(df['SUN_OPEN'], format='%H:%M:%S').dt.time
        df['SUN_CLOSE']=pandas.to_datetime(df['SUN_CLOSE'], format='%H:%M:%S').dt.time

        df.dropna(subset=['LOCATION'],inplace = True)
        df.dropna(subset=['START_DATE'],inplace = True)
        df.dropna(subset=['END_DATE'],inplace = True)

        df = df.replace(pandas.NaT, None)

        df = df[pandas.to_datetime(df.START_DATE).isin(availableDates)]
        df = df[pandas.to_datetime(df.END_DATE).isin(availableDates)]
        df = df[df.LOCATION.isin(availableLocations)]

        finalRows = len(df.index)

        metaData = {
            'cleanedData': df,
            'originalRows': initialRows,
            'cleanedRows': finalRows,
            'blanksFound': blanksCount
        }

        return metaData
    
    else:
        print('Aborted proceedure. Incorrect columns found')
        return -1