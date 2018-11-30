from config import _export_dir, _data_dir
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, shape
from sklearn import preprocessing, neighbors
from shapely.ops import nearest_points


shp_dir = '../airbnb/districts_shp/'

portugal = gpd.read_file(shp_dir+'gadm36_PRT.gpkg')\
            .rename(columns={'NAME_0':'country','NAME_1':'distrito', 'NAME_2':'concelho', 'NAME_3':'municipio' })\
            [['country','distrito','concelho','municipio','geometry']]

#portugal = portugal[portugal['distrito']]

distritos = portugal[['distrito', 'geometry']].dissolve('distrito').reset_index()
concelhos = portugal[['concelho', 'geometry']].dissolve(by='concelho').reset_index()
municipios = portugal[['municipio', 'geometry']]

# import the data we want to label
cdr_cell = pd.read_csv(_export_dir+'CDR_cellsites_preprocessed.csv')\
                        .reset_index()#[['cell_id', 'longitude', 'latitude']].reset_index()


def generate_point(row):
    return Point(row['longitude'],row['latitude'])

cdr_cell['point'] = cdr_cell.apply(generate_point, axis=1)

def label_location(row, gpd_table):
    for num in range(len(gpd_table)):
        check = gpd_table['geometry'][num].contains(row['point'])
        if check:
            return gpd_table[gpd_table.columns[0]][num]


cdr_cell['distrito'] = cdr_cell.apply(lambda x: label_location(x, distritos), axis=1)
cdr_cell['concelho'] = cdr_cell.apply(lambda x: label_location(x, concelhos), axis=1)
cdr_cell['municipio'] = cdr_cell.apply(lambda x: label_location(x, municipios), axis=1)

def knn_classifier(target, n_neighbors):
    X = cdr_cell[cdr_cell[target].notnull()][['latitude','longitude']]
    y = cdr_cell[cdr_cell[target].notnull()][target]
    clf = neighbors.KNeighborsClassifier(n_neighbors)
    clf.fit(X, y)
    try:
        knn_prediction = clf.predict(cdr_cell[cdr_cell[target].isnull()][['latitude','longitude']])
        cdr_cell.loc[cdr_cell[target].isnull(), target] = knn_prediction
    except ValueError:
        print('No observations left to classify!')
    

knn_classifier('municipio', 3)
knn_classifier('concelho', 3)
knn_classifier('distrito', 3)

#--------------------------------------------------------------------------------#
#-------------------------------- POI Assignment --------------------------------#
#--------------------------------------------------------------------------------#

cdr_cell
poi = pd.read_csv('../deliverable_august/other_data/poi/all_poi.csv')\
        .rename(columns={'Nome und': 'poi',
                         'Tipo de poi':'poi_type',
                         'Coordenada X':'longitude', 
                         'Coordenada Y':'latitude',
                         'field_poi_reg_loc':'loc_label2'
                        })

geometry = [Point(xy) for xy in zip(poi.longitude, poi.latitude)]
poi = poi.drop(['longitude', 'latitude'], axis=1)
crs = {'init': 'epsg:4326'}
poi = gpd.GeoDataFrame(poi, crs=crs, geometry=geometry)


def nearest(point, poi):
    poi['dist'] = poi.apply(lambda x: point['point'].distance(x['geometry']), axis=1) 
    return poi.iloc[poi['dist'].argmin()]['poi']

cdr_cell['poi'] = cdr_cell.apply(lambda x: nearest(x,poi), axis=1)

cdr_cell[['cell_id', 'distrito', 'concelho', 'municipio', 'poi']].to_csv(_export_dir+'region_labels.csv', index=False)

def get_coords(val,_type):
    if _type == 'longitude':
        return val.x
    if _type == 'latitude':
        return val.y

municipios['centroid'] = municipios.centroid
municipios['latitude'] = municipios['centroid'].apply(lambda val: get_coords(val, 'latitude'))
municipios['longitude'] = municipios['centroid'].apply(lambda val: get_coords(val, 'longitude'))

municipios[['municipio', 'latitude', 'longitude']].to_csv(_export_dir+'municipios_helper.csv', index=False)




