#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 11 16:40:51 2018

@author: joaofonseca
"""

import pandas as pd

data = '../data/'

continentes2 = pd.read_csv(data+'continentes2.csv')
country_features = pd.read_csv(data+'country_features.csv')
linguas_moedas = pd.read_csv(data+'linguas_moedas.csv')
mccmmc_optimized_new = pd.read_csv(data+'mccmmc_optimized_new.csv')
site_lookup_outubro = pd.read_csv(data+'site_lookup_outubro.csv')
tac_lookup = pd.read_csv(data+'tac_lookup.csv')
union_all = pd.read_csv(data+'union_all.csv')

table_list = {
        'continentes2': continentes2,
        'country_features': country_features,
        'linguas_moedas': linguas_moedas,
        'mccmmc_optimized_new': mccmmc_optimized_new,
        'site_lookup_outubro': site_lookup_outubro,
        'tac_lookup': tac_lookup,
        'union_all': union_all
        }

for table in table_list:
    print(table)
    print(list(table_list[table].columns))
    print('\n')
    
for table in table_list:
    print(table)

tac_lookup

df = pd.read_csv('../data/output/CDR_events_preprocessed.csv')

# =============================================================================
# plot map with new nodes' locations
# =============================================================================
import plotly.graph_objs as go
import plotly

mapbox_token = 'pk.eyJ1Ijoiam9hb2ZvbnNlY2EiLCJhIjoiY2picXB3cDVvMDczYjJ3bzBxNDV3dGI0MSJ9.XpQDNjTuMAM-xckGln0KrA'


new_nodes = pd.read_csv('../data/tourist_attractions_lisbon.txt')

data = go.Data([
        go.Scattermapbox(
                lat = new_nodes['Latitude'],
                lon = new_nodes['Longitude'],
                mode='markers',
                marker=go.Marker(size= 5,
                                 color='red' ),
                text = new_nodes['Place Name']
                )
        ])

layout = go.Layout(
    title='Location of listings',
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_token,
        bearing=0,
        style='light',
        center=dict(
            lat=39.64,
            lon=-7.95,
        ),
        pitch=0,
        zoom=4.2
    ),
)

wonder_map = go.Figure(data=data, layout=layout)

#generate interactive visualization
plotly.offline.plot(wonder_map, filename='../../lisbon_report/thesis_support_docs/' +'tourist_attractions.html', show_link=False, auto_open=False)

# =============================================================================
# voronoi diagram of new nodes
# =============================================================================

from geoprocess import GeoProcess
import json


new_nodes['lon'] = new_nodes['Longitude']
new_nodes['lat'] = new_nodes['Latitude']
new_nodes['cellid'] = new_nodes['Place Name']
nodes_clean = new_nodes[['cellid', 'lon', 'lat']]



import geopandas as gpd

def make_voronoi_in_shp( points, shape):
    """ Make a voronoi diagram geometry out of point definitions and embed it in a
    shape.
    :param: points (Geopandas.GeoDataFrame): The centroid points for the voronoi
    :param: shape (Geopandas.GeoDataFrame): The shapefile to contain the voronoi inside
    :return: Geopandas.GeoDataFrame: The polygon geometry for the voronoi diagram
    embedded inside the shape
    """

    # epsg (int): spatial reference system code for geospatial data
    voronoi_geo = GeoProcess.create_voronoi(points)
    voronoi_geo_in_shape = GeoProcess.get_points_inside_shape(voronoi_geo, shape)

    shape_with_voronoi = gpd.sjoin(points, voronoi_geo_in_shape, how="inner",
                                   op='within')

    del shape_with_voronoi['geometry']

    return voronoi_geo_in_shape.merge(shape_with_voronoi, left_index=True,
                                      right_on='index_right')












print('Generating Voronoi cells...')
nodes_clean_list = GeoProcess.convert_point_data_to_data_frame(nodes_clean)
#voronoi = GeoProcess.create_voronoi(nodes_clean_list)



#import geopandas as gpd
from shapely.geometry import Point, Polygon

shape_vertex = [
                Point([38.580287, -9.570982]), 
                Point([38.657462,-8.623532]),
                Point([39.019420, -8.849336]),
                Point([39.043499, -9.799979])
                ]
poly = Polygon([[p.x, p.y] for p in shape_vertex])

voronoi = make_voronoi_in_shp(points = nodes_clean_list, shape = poly)


json_data_string = voronoi[['geometry']].to_json()
json_data = json.loads(json_data_string)

with open('../../lisbon_report/thesis_support_docs/'+'new_nodes_voronoi_dict.json','w') as json_file:
    json.dump(json_data, json_file)















