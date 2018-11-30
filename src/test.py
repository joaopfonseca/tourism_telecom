from config import _export_dir, _data_dir
import pandas as pd
import fiona
from shapely.geometry import Point, shape
from sklearn import preprocessing, neighbors


shp_dir = '../pt_regions_shapefiles/districts_shp/'

shp_file = fiona.open(shp_dir+'PRT_adm2.shp')

# import shapefile
regioes = pd.read_csv(shp_dir+'PRT_adm2.csv')

# apply to ID_2
def get_region_shape(value):
    return shape(shp_file[value-1]['geometry'])

regioes['geometry'] = regioes['ID_2'].apply(get_region_shape)
regioes = regioes[['NAME_1', 'NAME_2', 'geometry']]
regioes = regioes.rename(index=str ,columns={'NAME_1':'distrito', 'NAME_2':'concelho', 'geometry':'geometry'})

# import the data we want to label
cdr_cell = pd.read_csv(_export_dir+'CDR_cellsites_preprocessed.csv')\
                        .reset_index()#[['cell_id', 'longitude', 'latitude']].reset_index()


def generate_point(row):
    return Point(row['longitude'],row['latitude'])

cdr_cell['point'] = cdr_cell.apply(generate_point, axis=1)

def label_location(row, which):
    for num in range(len(regioes)):
        check = regioes['geometry'][num].contains(row['point'])
        if check:
            if which == 'distrito':
                return regioes['distrito'][num]
            elif which == 'concelho':
                return regioes['concelho'][num]


cdr_cell['distrito'] = cdr_cell.apply(lambda x: label_location(x, 'distrito'), axis=1)
cdr_cell['concelho'] = cdr_cell.apply(lambda x: label_location(x, 'concelho'), axis=1)

def knn_classifier(target, n_neighbors):
    n_neighbors = 3
    X = cdr_cell[cdr_cell[target].notnull()][['latitude','longitude']]
    y = cdr_cell[cdr_cell[target].notnull()][target]
    clf = neighbors.KNeighborsClassifier(n_neighbors)
    clf.fit(X, y)
    knn_prediction = clf.predict(cdr_cell[cdr_cell[target].isnull()][['latitude','longitude']])
    cdr_cell.loc[cdr_cell[target].isnull(), target] = knn_prediction

knn_classifier('concelho', 3)
knn_classifier('distrito', 3)

cdr_cell[['cell_id', 'distrito', 'concelho']].to_csv(_export_dir+'region_labels.csv', index=False)
