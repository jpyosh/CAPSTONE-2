import pandas, datetime
import numpy as np
from sklearn.cluster import KMeans 
import plotly.express as px

from sklearn.datasets import make_moons
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

def createLineGraph(df, title):
    pandas.DataFrame(df)
    fig = px.line(df, x=df.index, y='total', title=title)
    return fig

def createBarGraph(df, title):
    pandas.DataFrame(df)
    fig = px.bar(df, x=df.index, y='total', title=title)
    return fig

def createBarGraphbyGender(df):
    pandas.DataFrame(df)
    fig = px.bar(x=['male','female'], y=[df['male'].sum(), df['female'].sum()])
    return fig

def createBarGraphbyOrigin(df):
    pandas.DataFrame(df)
    fig = px.bar(x=['foreign','domestic'], y=[df['foreign'].sum(), df['domestic'].sum()])
    return fig

def createScatterPlotGender(df, title):
    pandas.DataFrame(df)
    fig = px.scatter(df, x='male', y='female', title=title)
    return fig

def createKmeansClusterDate2d(df, x, y, clusters):
    kmeans = KMeans(n_clusters=clusters, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(df[[x,y]])
    fig = px.scatter(df, x=x, y=y, color='cluster', text=df.index.date, color_continuous_scale='jet')
    fig.update_traces(textposition='top center')
    return fig

def createKmeansCluster2d(df, x, y, clusters):
    kmeans = KMeans(n_clusters=clusters, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(df[[x,y]])
    fig = px.scatter(df, x=x, y=y, color='cluster', text=df.index, color_continuous_scale='jet')
    fig.update_traces(textposition='top center')
    return fig

def createWeeklyHeatMap(df):
    new_df = df.groupby(['location','time_month'])['total'].sum().reset_index()
    new_df = new_df.pivot(index='location', columns='time_month')['total'].fillna(0)
    print(new_df)
    fig = px.imshow(new_df, x=new_df.columns, y=new_df.index)
    fig.update_layout(width=500,height=500)
    return fig