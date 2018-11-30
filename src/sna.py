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



def get_dynamic_edgelist(data):
    """ Make an edge list for all of the sequential visits of one site to the next
    in a day per user. Each edge is directed. There is a dummy start node to
    indicate the transition from being home to the first site visited that day """
    
    data['total_people'] = 1    
    
    edges = data.groupby(["user_id", "date_time", "date",
                          "cell_id"]).sum()["total_people"].to_frame()
    edges.reset_index(inplace=True)

    # start is the name of the dummy node for edges from home to the first location visited
    edges["from"] = 'dummy_start_node'
    edges["to"] = edges["cell_id"]

    make_link = (edges["user_id"].shift(1) == edges["user_id"]) & \
                (edges["date"].shift(1) == edges["date"])

    edges["from"][make_link] = edges["cell_id"].shift(1)[make_link]
    dynamic_edgelist = edges[["from", "to", "total_people", "date_time"]]

    dynamic_edgelist = dynamic_edgelist[dynamic_edgelist['from'] != dynamic_edgelist['to'] ]

    return dynamic_edgelist



# =============================================================================
# 
# =============================================================================

# radius, lat, lon of area of voronoi
# 

def create_voronoi(points):
    """ Make a voronoi diagram geometry out of point definitions
    :param: points (Geopandas.GeoDataFrame): The centroid points for the voronoi
    :return: Geopandas.GeoDataFrame: The polygon geometry for the voronoi diagram
    """

    np_points = [np.array([pt.x, pt.y]) for pt in np.array(points.geometry)]
    vor = Voronoi(np_points)

    lines = [
        shp.LineString(vor.vertices[line])
        for line in vor.ridge_vertices
        if -1 not in line
    ]

    voronoi_poly = sp.ops.polygonize(lines)
    crs = {'init': 'epsg:' + str(4326)}
#        return gpd.GeoDataFrame(crs=crs, geometry=list(voronoi_poly)) \
#            .to_crs(epsg=4326)
    
    geodataframe = gpd.GeoDataFrame(crs=crs, geometry=list(voronoi_poly)) \
        .to_crs(epsg=4326)
    #geodataframe['centroid'] = geodataframe.centroid
    
    return geodataframe


def create_circle(lat, lon, radius=18, num_points=20):
    """ Create the approximation or a geojson circle polygon
    :param: lat: the center latitude for the polygon
    :param: lon: the center longitude for the polygon
    :param: radius (int): the radius of the circle polygon
    :param: num_points (int): number of discrete sample points to be generated along the circle
    :return: list of lat/lon points defining a somewhat circular polygon
    """

    points = []
    for k in range(num_points):

        angle = math.pi * 2 * k / num_points
        dx = radius * math.cos(angle)
        dy = radius * math.sin(angle)

        new_lat = lat + (180 / math.pi) * (dy / 6378137)
        new_lon = lon + (180 / math.pi) * (dx / 6378137) / math.cos(
            lat * math.pi / 180)

        points.append([round(new_lon, 7), round(new_lat, 7)])

    return points


def convert_point_data_to_data_frame(data):
    """ Takes a data set with latitude and longitude columns and returns a Geopandas
    GeoDataFrame object.
    :param: data (Pandas.DataFrame): the lat/lon data to convert to GeoDataFrame
    :return: GeoPandas.GeoDataFrame: the contents of the supplied data in the
    format of a GeoPandas GeoDataFrame
    """

    zipped_data = zip(data['lon'], data['lat'])
    geo_points = [shp.Point(xy) for xy in zipped_data]
    crs = {'init': 'epsg:' + str(4326)}

    return gpd.GeoDataFrame(data, crs=crs, geometry=geo_points) \
        .to_crs(epsg=4326)





def generate_artificial_nodes(site_list, radius=30000, lat=38.751296, lon=-9.2180615):
    # limiting rangetoarea of interest
    weird_circle = create_circle(lat, lon, radius=radius, num_points=20)
    weird_circle = shp.Polygon(weird_circle)

    #site_list = pd.read_csv(_export_dir+'CDR_cellsites_preprocessed.csv', encoding='utf-8', sep=',', index_col=None, decimal='.')

    site_list['lon'] = site_list['longitude']
    site_list['lat'] = site_list['latitude']
    site_list['cellid'] = site_list['cell_id']
    #site_list['real_cellid'] = site_list['cellid']
    site_list_clean = site_list[['cellid', 'lon', 'lat']]

    site_point_list = convert_point_data_to_data_frame(site_list_clean)
    site_point_list['is_area_of_interest'] = site_point_list['geometry'].intersects(weird_circle)
    points_of_interest = site_point_list[site_point_list['is_area_of_interest']]

    print('Generating Voronoi cells...')
    voronoi = create_voronoi(site_point_list)
    
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
    nodes_clean_list = convert_point_data_to_data_frame(nodes_clean)
    voronoi2 = create_voronoi(nodes_clean_list) # this needs to be integrated in the table
    #voronoi2['voronoi_polygon'] = voronoi2['geometry']
    voronoi2['geometry']=voronoi2.intersection(weird_circle) # this is redundant, but it stays to ensure there are no errors
    
    voronoi2['cell_center'] = 'not found'
    voronoi2['node_name'] = 'not found'
    for number in range(len(nodes_clean_list)):
        for cell in range(len(voronoi2)):
            if voronoi2['geometry'][cell].contains(nodes_clean_list['geometry'][number]):
                voronoi2['cell_center'][cell] = nodes_clean_list['geometry'][number]
                voronoi2['node_name'][cell] = nodes_clean_list['cellid'][number]
                break
    
    
    
#    def convert_to_point(row):
#        return shp.Point(row['Latitude'], row['Longitude'])
#
#    new_nodes['point'] = new_nodes.apply(convert_to_point, axis=1)
    
#    #voronoi2 = voronoi2.reset_index()
#    def identify_node(cell, node_list):
#        for node in range(len(node_list)):
#            if cell.intersects(node_list['geometry'][node]):
#                return node_list['cellid'][node]
#        return 'no_match'
#    
#    voronoi2['node_name'] = voronoi2['geometry'].apply(lambda x: identify_node(x, nodes_clean_list))
    
    def get_info(point, voronoi_diagram, which_info):
        for poly in range(len(voronoi_diagram)):
            if voronoi_diagram['geometry'][poly].contains(point):
                if which_info == 'node_name':
                    return voronoi_diagram['node_name'][poly]
                elif which_info == 'voronoi_polygon':
                    return voronoi_diagram['geometry'][poly]
                elif which_info == 'cell_center':
                    return voronoi_diagram['cell_center'][poly]
                else:
                    raise Exception('Info doesn\'t exist')
        return 'not_in_lisbon'
    
    points_of_interest['cellid2']= points_of_interest['cellid']
    points_of_interest['cellid'] = points_of_interest['geometry'].apply(lambda x: get_info(x, voronoi2, 'node_name'))
    points_of_interest['voronoi_polygon'] = points_of_interest['geometry'].apply(lambda x: get_info(x, voronoi2, 'voronoi_polygon'))
    points_of_interest['cell_center'] = points_of_interest['geometry'].apply(lambda x: get_info(x, voronoi2, 'cell_center'))
    points_of_interest = points_of_interest[points_of_interest['cellid']!='not_in_lisbon']\
    [['cellid', 'cellid2', 'lon', 'lat', 'geometry', 'voronoi_polygon', 'cell_center']]

    # added in june 27, fix for AttributeError: 'str' object has no attribute 'x'
    voronoi2= voronoi2[voronoi2['cell_center']!='not found']
    ##########
    
    json_data_string2 = voronoi2[['geometry']].to_json()
    json_data2 = json.loads(json_data_string2)
    
    
    with open(_export_dir+'new_nodes_voronoi_dict.json','w') as json_file:
        json.dump(json_data2, json_file)
    
    return {'tower_cells_to_new_nodes':points_of_interest, 'voronoi_cells':voronoi2}








