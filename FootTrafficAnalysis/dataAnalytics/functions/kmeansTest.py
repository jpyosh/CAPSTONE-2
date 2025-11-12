import pandas 
import numpy

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def KmeansClusteringModel(df, n_clusters):

    genderdf = (df[['location','time_year','male', 'female']].groupby(['location', 'time_year']).sum()[['male', 'female']])
    origindf = (df[['location','time_year','domestic', 'foreign']].groupby(['location', 'time_year']).sum()[['domestic', 'foreign']])

    genderdf = genderdf[genderdf.sum(axis=1) != 0]
    origindf = origindf[origindf.sum(axis=1) != 0]

    genderModel = KMeans(n_clusters=n_clusters, random_state=7)
    gender_labels = genderModel.fit_predict(genderdf)
    sil_gender = silhouette_score(genderdf, gender_labels)

    originModel = KMeans(n_clusters=n_clusters, random_state=7)
    origin_labels = originModel.fit_predict(origindf)
    sil_origin = silhouette_score(origindf, origin_labels)

    genderdf['clusters'] = gender_labels
    origindf['clusters'] = origin_labels

    return { 'gender_model': genderdf.reset_index(), 'origin_model': origindf.reset_index(), 'gender_res': sil_gender, 'origin_res': sil_origin}

def selectBestKmeans(df):
    attempts = range(2,11)
    clusters = []
    for i in attempts:
        clusters.append(KmeansClusteringModel(df, i))

    best_orig = 0
    best_orig_df = 0
    for i in clusters:
        if i['origin_res'] > best_orig:
            best_orig = i['origin_res']
            best_orig_df = i['origin_model']

    best_gend = 0
    best_gend_df = 0
    for i in clusters:
        if i['gender_res'] > best_gend:
            best_gend = i['gender_res']
            best_gend_df = i['gender_model']

    print("Clustering Results:")
    print("Best Gender Results:", best_gend)
    print("Best Gender Clusters:", best_gend_df['clusters'].nunique())
    print("Best Origin Results:", best_orig)
    print("Best Origin Clusters:", best_orig_df['clusters'].nunique())

    return { 'gender_model': best_gend_df, 'origin_model': best_orig_df, 'gender_res': best_gend, 'origin_res': best_orig}
