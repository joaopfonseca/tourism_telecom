#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from config import _export_dir, _data_dir
import pandas as pd
import shapely as sp
import shapely.geometry as shp
import json
import math
import geopandas as gpd
import numpy as np
from scipy.spatial import Voronoi
from geoprocess import GeoProcess

from config import _export_dir, _data_dir
from events_preprocess import preprocess, preprocess_cells
from sna import get_dynamic_edgelist, generate_artificial_nodes, convert_point_data_to_data_frame, create_voronoi, create_circle
from utils import generate_flows_in_json_file





"""

site_list = pd.read_csv(_export_dir+'CDR_cellsites_preprocessed.csv', encoding='utf-8', sep=',', index_col=None, decimal='.')
radius=30000
lat=38.751296
lon=-9.2180615




# limiting rangetoarea of interest
weird_circle = GeoProcess.create_circle(lat, lon, radius=radius, num_points=20)
weird_circle = shp.Polygon(weird_circle)


site_list['lon'] = site_list['longitude']
site_list['lat'] = site_list['latitude']
site_list['cellid'] = site_list['cell_id']
site_list_clean = site_list[['cellid', 'lon', 'lat']]

site_point_list = GeoProcess.convert_point_data_to_data_frame(site_list_clean)
site_point_list['is_area_of_interest'] = site_point_list['geometry'].intersects(weird_circle)
points_of_interest = site_point_list[site_point_list['is_area_of_interest']]

print('Generating Voronoi cells...')
voronoi = GeoProcess.create_voronoi(site_point_list)

voronoi['geometry']=voronoi.intersection(weird_circle)

json_data_string = voronoi[['geometry']].to_json()
json_data = json.loads(json_data_string)

with open(_export_dir+'cdr_voronoi_dict.json','w') as json_file:
    json.dump(json_data, json_file)


# generating voronoi for new nodes - ARTIFICIAL NODES!
new_nodes = pd.read_csv(_data_dir+'tourist_attractions_lisbon.txt')
new_nodes['lon'] = new_nodes['Longitude']
new_nodes['lat'] = new_nodes['Latitude']
new_nodes['cellid'] = new_nodes['Place Name']
nodes_clean = new_nodes[['cellid', 'lon', 'lat']]
nodes_clean_list = GeoProcess.convert_point_data_to_data_frame(nodes_clean)
voronoi2 = GeoProcess.create_voronoi(nodes_clean_list) # this needs to be integrated in the table

voronoi2['geometry']=voronoi2.intersection(weird_circle)

#voronoi2 = voronoi2.reset_index()

def identify_node(cell, node_list):
    for node in range(len(node_list)):
        if cell.intersects(node_list['geometry'][node]):
            return node_list['cellid'][node]
    return 'no_match'

voronoi2['node_name'] = voronoi2['geometry'].apply(lambda x: identify_node(x, nodes_clean_list))

def get_new_id(point, voronoi_diagram):
    for poly in range(len(voronoi_diagram)):
        if point.intersects(voronoi_diagram['geometry'][poly]):
            return voronoi_diagram['node_name'][poly]
    return 'not_in_lisbon'

points_of_interest['cellid2']= points_of_interest['cellid']
points_of_interest['cellid'] = points_of_interest['geometry'].apply(lambda x: get_new_id(x, voronoi2))
points_of_interest = points_of_interest[points_of_interest['cellid']!='not_in_lisbon'][['cellid', 'cellid2', 'lon','lat', 'geometry']]

json_data_string2 = voronoi2[['geometry']].to_json()
json_data2 = json.loads(json_data_string2)

with open(_export_dir+'new_nodes_voronoi_dict.json','w') as json_file:
    json.dump(json_data2, json_file)

"""


"""
df = pd.read_csv(_data_dir+'union_all.csv')
df2 = pd.read_csv(_export_dir+'CDR_cellsites_preprocessed.csv')
df3 = pd.read_csv(_data_dir+'mccmmc_optimized_new.csv')
new_node_ids= generate_artificial_nodes(df2, 30000, 38.751296, -9.2180615)




def conditional_float_to_string(param):
    if np.isnan(param):
        new_param = 'none'
    else:
        new_param=str(int(param))
    return new_param

def get_mcc(param):
    return param[:3]


#    df = pd.read_csv(_data_dir+'union_all.csv')
df['user_id'] = df['union_all.client_id']
df['date_time'] = df['union_all.enddate_']
df['cellid_df1'] = df['union_all.cellid']
df['lac_'] = df['union_all.lac_']
df['protocol_df1'] = df['union_all.protocol_']
df['edited_mcc'] = df['union_all.mccmnc'].astype(str).apply(get_mcc)
df['tac'] = df['union_all.tac']
df['datekey'] = df['union_all.datekey']
df['real_cellid'] = df['union_all.cellid'].apply(conditional_float_to_string) + df['lac_'].apply(conditional_float_to_string) + df['union_all.protocol_'].apply(conditional_float_to_string)
df['real_cellid'] = df['real_cellid'].astype(str)


#    df3 = pd.read_csv(_data_dir+'mccmmc_optimized_new.csv')
new_keys3 = []
for key in df3.keys():
    new_key= key.replace('mccmnc_optimized_new.', '')
    new_keys3.append(new_key)
df3.columns = new_keys3

def add_zeros(param):
    if (param != 'none') and int(param)<10:
        param = '0'+param
    return param

df3['edited_mcc'] = df3['mcc'].astype(str)
df3 = df3[df3['country'] != 'Guam'].drop(['network','mnc', 'mnc_', 'mcc_'], axis=1).drop_duplicates()

table_merge1 = pd.merge(df, df2, on='real_cellid', how='left')
df_final= pd.merge( table_merge1, df3, on='edited_mcc', how='left')
df_final['user_origin'] = df_final['country']
df_final['cell_id'] = df_final['real_cellid']
df_final['cellid2'] = df_final['real_cellid']
dataframe = df_final[['user_id','date_time','user_origin','cell_id','latitude','longitude', 'cellid2']]

refs = new_node_ids[['cellid', 'cellid2']]

df_merged = pd.merge( dataframe, refs, on='cellid2', how='left' )
df_merged = df_merged[df_merged['cellid'].notnull()]

df_merged['date'] = pd.to_datetime(df_merged['date_time']).dt.date
df_merged['rounded_time'] = pd.to_datetime(df_merged['date_time']).dt.hour
df_merged['time'] = pd.to_datetime(df_merged['date_time']).dt.time

events = pd.DataFrame(df_merged.groupby('user_id', as_index=False).size().reset_index())
events.columns = ['user_id', 'total_events']
df_merged = events.merge(df_merged, on='user_id')

activity=df_merged[['user_id','date']].drop_duplicates()
days_active = activity.groupby('user_id', as_index=False)['date'].count()
days_active.columns = ['user_id', 'days_active']
df_merged = df_merged.merge(days_active, on='user_id')
df_merged['cell_id'] = df_merged['cellid']
df_merged = df_merged[['user_id', 'cell_id', 'total_events', 'date_time', 'user_origin',
                       'latitude', 'longitude', 'date', 'rounded_time',
                       'time', 'days_active']]

#        # filter out bots
#        df['is_bot'] = (df['total_calls'] / df['days_active']) > self.params.bot_threshold
#        df = df[df['is_bot'] == False]
#
#        # filter out customers who made less than N calls
#        calls_in_florence = df.groupby('user_id', as_index=False)['total_calls'].count()
#        users_to_keep = list(calls_in_florence[calls_in_florence['total_calls'] >= self.params.minimum_total_calls]['user_id'])
#        df = df[df['user_id'].isin(users_to_keep)]

df_merged.to_csv(_export_dir+'CDR_events_preprocessed.csv', index=False)

"""




radius=30000
lat=38.751296
lon=-9.2180615

weird_circle = create_circle(lat, lon, radius=radius, num_points=20)
weird_circle = shp.Polygon(weird_circle)






new_nodes = pd.read_csv(_data_dir+'tourist_attractions_lisbon.txt')
new_nodes['lon'] = new_nodes['Longitude']
new_nodes['lat'] = new_nodes['Latitude']
new_nodes['cellid'] = new_nodes['Place Name']
nodes_clean = new_nodes[['cellid', 'lon', 'lat']]
nodes_clean_list = convert_point_data_to_data_frame(nodes_clean)
voronoi2 = create_voronoi(nodes_clean_list) # this needs to be integrated in the table
#voronoi2['voronoi_polygon'] = voronoi2['geometry']
voronoi2['geometry']=voronoi2.intersection(weird_circle) # this is redundant, but it stays to ensure there are no errors

### 

#def convert_to_point(row):
#    return shp.Point(row['Latitude'], row['Longitude'])

#new_nodes['point'] = new_nodes.apply(convert_to_point, axis=1)

voronoi2['cell_center'] = 'not found'
for number in range(len(nodes_clean_list)):
    for cell in range(len(voronoi2)):
        if voronoi2['geometry'][cell].intersects(nodes_clean_list['geometry'][number]):
            voronoi2['cell_center'][number] = nodes_clean_list['geometry'][cell]
            break

new_nodes[['Place Name', 'point']]

    








