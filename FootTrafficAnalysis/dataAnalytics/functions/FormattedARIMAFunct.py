import pandas
import numpy
import datetime

from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from sktime.performance_metrics.forecasting import mean_absolute_scaled_error, mean_squared_percentage_error
from dateutil.relativedelta import relativedelta
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, ExponentialSmoothing

import itertools

import warnings
warnings.filterwarnings('ignore')

import numpy as np

def smape(A, F):
    return 100/len(A) * np.sum(2 * np.abs(F - A) / (np.abs(A) + np.abs(F)))

def arimaPredict(newdf, granularity, selectedArea):
    selectedGranularityColumn = granularity
    selectedArea = selectedArea
    print('starting analysis for: ', selectedArea)
    logMSG = ['starting analysis for: ' + selectedArea]
    
    orig = newdf
    orig[selectedGranularityColumn] = pandas.to_datetime(orig[selectedGranularityColumn])
    orig = orig.set_index(selectedGranularityColumn)
    df = orig[['male', 'female', 'sexUnknown', 'uncategorized', 'location']]
    df = df[df.location == selectedArea]
    df['total'] = df[['male', 'female', 'sexUnknown', 'uncategorized']].sum(axis=1)
    df = df.groupby(selectedGranularityColumn).sum()
    df = df.drop(columns=['male', 'female', 'sexUnknown', 'uncategorized', 'location'])
    
    #Play around with split ratio
    split_ratio = 0.8
    split_index = int(len(df) * split_ratio)
    
    train = df.iloc[:split_index]
    trainOrig = train
    train = train
    test = df.iloc[split_index:]
    
    p = range(0, 5)
    d = range(0, 5)
    q = range(0, 5)
    pdq = list(itertools.product(p, d, q))

    best_val = numpy.inf
    best_order = None

    for order in pdq:
        try:
            model = ARIMA(train, order=order)
            results = model.fit()
            results.get_forecast(len(test.index)).conf_int(alpha = 0.05)
            testPred = results.predict(start = test.index[0], end = test.index[-1])
            mse = mean_absolute_scaled_error(test, testPred, y_train=train)
            if mse < best_val:
                best_val = mse
                best_order = order
        except:
            continue
    
    ARIMAmodel = ARIMA(train, order = best_order)
    ARIMAmodel = ARIMAmodel.fit()

    y_pred = ARIMAmodel.get_forecast(len(test.index))
    y_pred_df = y_pred.conf_int(alpha = 0.05) 
    y_pred_df["Predictions"] = ARIMAmodel.predict(start = y_pred_df.index[0], end = y_pred_df.index[-1])
    y_pred_df.index = test.index
    y_pred_out = y_pred_df["Predictions"]         

    future = pandas.DataFrame(ARIMAmodel.predict(start = y_pred_df.index[-1] + datetime.timedelta(days=1), end = y_pred_df.index[-1] + relativedelta(months=+7)))
    
    smoothing = future.ewm(span = 2).mean()
    difference = future - smoothing
    pos = (difference > 0).sum().sum()/len(difference)
    neg = (difference < 0).sum().sum()/len(difference)
    
    final1 = trainOrig
    final2 = test
    future = future.rename(columns={'predicted_mean': 'total'})
    future['type'] = 'prediction'
    
    totaldf = pandas.concat([final1, final2, future], axis=0)
    totaldf['type'] = totaldf['type'].fillna('actual')
    
    formattedData = pandas.DataFrame()
    
    formattedData.index = df.index
    formattedData['value'] = df['total']
    formattedData['valueType'] = 'actual'
        
    for key, value in pandas.DataFrame(y_pred_out).iterrows():
        new_rows = pandas.DataFrame({"value": value["Predictions"], "valueType": 'prediction'}, index=[key])
        formattedData = pandas.concat([formattedData, new_rows])
    
    for key, value in future.iterrows():
        new_rows = pandas.DataFrame({"value": value["total"], "valueType": 'prediction'}, index=[key])
        formattedData = pandas.concat([formattedData, new_rows])
        
    for key, value in pandas.DataFrame(ARIMAmodel.fittedvalues).iterrows():
        new_rows = pandas.DataFrame({"value": value[0], "valueType": 'prediction'}, index=[key])
        formattedData = pandas.concat([formattedData, new_rows])
    
    formattedData['location'] = selectedArea
        
    mspe = mean_squared_percentage_error(y_pred_out, test)
    mape = mean_absolute_percentage_error(y_pred_out, test)
    mase = mean_absolute_scaled_error(test, y_pred_out, y_train=train)
    smapeVal = smape(test['total'], y_pred_out)
    print(selectedArea, 'Values:')
    print('MSPE: ', round(mspe,2), 
          'MAPE: ', round(mape,2),
          'MASE: ', round(mase,2),
          'SMAPE: ', round(smapeVal,2))
    
    logMSG.append(selectedArea + ' Values: ')
    logMSG.append('MSPE: ' + str(round(mspe,2)))
    logMSG.append('MAPE: ' + str(round(mape,2)))
    logMSG.append('MASE: ' + str(round(mase,2)))
    logMSG.append('SMAPE: ' + str(round(smapeVal,2)))
    
    lastAve = df['total'].tail(7).mean()

    futAve = future['total'].mean()
    
    if best_val < 1:
        acceptable = 1
    else:
        acceptable = 0
        sasFindings = sasAttempt(df)
        logMSG = logMSG + sasFindings.get('logs')
        if sasFindings.get('newMase') < best_val:
            formattedData = sasFindings.get('newPrediction')
            formattedData['location'] = selectedArea
            pos = sasFindings.get('pos')
            neg = sasFindings.get('neg')
            best_val = sasFindings.get('newMase')
            futAve = sasFindings.get('futAve')
        if sasFindings.get('newMase') < 1:
            acceptable = 1

    percIncrease = (futAve - lastAve)/lastAve
    print(percIncrease)
    
    finalData = {
        'dataframe': formattedData,
        'pos' : pos,
        'neg' : neg,
        'meetsStandard' : acceptable,
        'location' : selectedArea,
        'detailedVal' : best_val,
        'relativePref': percIncrease,
        'logs': logMSG
        }
    return finalData

def arimaPredictAll(df):
    locations =  df['location'].unique()
    predictions = []
    for item in locations:   
        predictions.append(arimaPredict(df, 'time_month', item))        
    return predictions

def sasAttempt(df):
    print('Values found inadequate Training Moving Average')
    model = SimpleExpSmoothing(df['total']).fit()
    pretest = model.fittedvalues

    model2 = ExponentialSmoothing(df['total'], trend='add').fit()
    pretest2 = model2.fittedvalues

    sasVal = mean_absolute_scaled_error(df['total'], pretest, y_train=df['total'])
    doubleVal = mean_absolute_scaled_error(df['total'], pretest2, y_train=df['total'])

    if sasVal < doubleVal:
        mase = mean_absolute_scaled_error(df['total'], pretest, y_train=df['total'])
    else:
        mase = mean_absolute_scaled_error(df['total'], pretest2, y_train=df['total'])
        model = model2
        pretest = pretest2
    smapeVal = smape(df['total'], pretest)
    
    formattedData = pandas.DataFrame()
    
    formattedData.index = df.index
    formattedData['value'] = df['total']
    formattedData['valueType'] = 'actual'
    
    for key, value in pandas.DataFrame(pretest).iterrows():
        new_rows = pandas.DataFrame({"value": value[0], "valueType": 'prediction'}, index=[key])
        formattedData = pandas.concat([formattedData, new_rows])
    
    for key, value in pandas.DataFrame(model.forecast(7)).iterrows():
        new_rows = pandas.DataFrame({"value": value[0], "valueType": 'prediction'}, index=[key])
        formattedData = pandas.concat([formattedData, new_rows])

    futureAve = model.forecast(7).mean()
        
    pos = 0
    neg = 0
    
    print('New Values:')
    print('MASE: ', round(mase,2),
          'SMAPE: ', round(smapeVal,2))  

    logMSG = ['Values found inadequate Training Moving Average','New Values: ','MASE: ' + str(round(mase,2)), 'SMAPE: ' + str(round(smapeVal,2))]
        
    return {'newMase': mase, 'newPrediction': formattedData, 'pos': pos, 'neg': neg, 'futAve': futureAve, 'logs': logMSG}