# -*- coding: utf-8 -*-
import pandas as pd
from config import constants, _export_dir, _data_dir
from geopandas.tools import sjoin
#import geopandas as gpd


from events_preprocess import preprocess
from sna import sna_preprocess, get_dynamic_edgelist

from geoprocess import GeoProcess
#from network_analysis import NetworkAnalysis
#from fountain_deck_gl import FountainViz

pd.options.mode.chained_assignment = None  # default='warn'

# =============================================================================
# preprocess cell/site data
# =============================================================================
print('Preprocessing cell/site data...')

print('_______________________________')


# =============================================================================
# preprocess events data
# =============================================================================
print('Preprocessing events data...')
preprocess() #table names/directories, and column names may need to be changed later on

# =============================================================================
# geomap site plotting using the Voronoi diagram generated
# =============================================================================

#awful visualization, but it works
#voronoi.plot(cmap='Set2', figsize=(10, 10))
#import matplotlib.pyplot as plt
#plt.show()

# =============================================================================
# Network Analysis
# =============================================================================
print('Creating the edge list...')
dfna = pd.read_csv(_export_dir+'CDR_events_preprocessed.csv')
edge_list = get_dynamic_edgelist(dfna)
edge_list.to_csv(_export_dir+'edge_list.csv', index=False)



print('Creating nodes list...')
import_nodes = pd.read_csv(_export_dir+'CDR_cellsites_preprocessed.csv')
list_of_nodes = []
for row in range(len(import_nodes)):
    node = (import_nodes['cell_id'][row],import_nodes['latitude'][row],import_nodes['longitude'][row],import_nodes['name_site'][row],import_nodes['concelho'][row])
    list_of_nodes.append(node)

nodes = list_of_nodes
edges = pd.read_csv(_export_dir+'edge_list.csv')
edges['weight'] = edges['total_people']
geometries = json_data













#from numba import jit
#@jit
#def associate_voronoi_to_cell_id():
#    voronoi['cell_id'] = 0
#    voronoi_left = len(voronoi)
#    voronoi_count_total= len(voronoi)
#    for voronoi_cell in range(len(voronoi)):
#        if voronoi_left % 50 == 0:
#            print(str((1-(voronoi_left/voronoi_count_total))*100)[:4]+'%')
#        voronoi_left = voronoi_left - 1
#        for centroid in range(len(site_point_list)):
#            is_centroid = voronoi['geometry'][voronoi_cell].intersects(site_point_list['geometry'][centroid])
#            if is_centroid:
#                voronoi['cell_id'][voronoi_cell] = site_point_list['cellid'][centroid]
#                break

def associate_voronoi_to_cell_id():
    avoronoi = voronoi
    asite_point_list = site_point_list[['cellid','geometry']]
    pointInPolys = sjoin(asite_point_list, avoronoi, how='right').reset_index()
    asite_point_list = asite_point_list.reset_index()
    pointInPolys = pointInPolys.merge(asite_point_list, on='index_left')
    return pointInPolys

print('Associating nodes to voronoi cells...')
voronoi_gpd = associate_voronoi_to_cell_id()
print('Checking if voronoi cell generation was successfull...')
for row in range(len(voronoi_gpd)):
    if not voronoi_gpd['geometry_x'][row].intersects(voronoi_gpd['geometry_y'][row]):
        print('error in row number:'+row, 'Cell IDX:'+voronoi_gpd['cellid_x'][row], 'Cell IDY:'+voronoi_gpd['cellid_x'][row])
for row in range(len(voronoi_gpd)):
    if not voronoi_gpd['cellid_x'][row] == voronoi_gpd['cellid_y'][row]:
        print('error in row number:'+row, 'Cell IDX:'+voronoi_gpd['cellid_x'][row], 'Cell IDY:'+voronoi_gpd['cellid_x'][row])


edges_pd = pd.read_csv(_export_dir+'edge_list.csv')




from random import randint

print('Generating json data file for flows analysis...')
def json_flows_file(voronoi_gpd, edges_pd):
    """
    voronoi_gpd: geometry, centroid
    edges: from, to, total_people, date_time
    """
    edges_pd['weight'] = edges_pd['total_people']
    voronoi_gpd['cell_id']=voronoi_gpd['cellid_x']

    d = dict(
            dict_number = range(len(voronoi_gpd)),
            cell_id = list(x for x in voronoi_gpd['cell_id'])
            )
    number_in_dict = pd.DataFrame(d).set_index('cell_id')

    #create flows dict
    def flows_in_cell_id(cell_id):
        cid = str(cell_id)
        flows = {}
        for flow in range(len(edges_pd[edges_pd['from']==cid])):
            try:
                flows[str(number_in_dict['dict_number'][edges_pd[edges_pd['from']==cid].reset_index()['to'][flow]])] = randint(9000,900000)#int(edges_pd[edges_pd['from']==cid].reset_index()['weight'][flow])
            except (KeyError, TypeError) as e:
                pass
        return flows # CHANGED FOR DEMONSTRATION, SEE LINE 163!!!!
# =============================================================================
# =============================================================================
# =============================================================================
# =============================================================================
# # # # 
# =============================================================================
# =============================================================================
# =============================================================================
# =============================================================================
    #getting data for voronoi cells
    features_data = []
    for cell in range(len(voronoi_gpd)):
        cell_id = voronoi_gpd['cell_id'][cell]
        geometry_coords = []
        for vertex in list(voronoi_gpd['geometry_x'][cell].exterior.coords):
            geometry_coords.append(list(vertex))
        
        
        
        geometry_data = dict(
                type = 'Feature',
                geometry = dict(
                        coordinates = [geometry_coords],
                        type = 'Polygon'
                        
                        ),
                properties = dict(
                        centroid = [voronoi_gpd['geometry_y'][cell].x, voronoi_gpd['geometry_y'][cell].y],
                        flows = flows_in_cell_id(cell_id),
                        name = cell_id
                        )
                )
        features_data.append(geometry_data)

    json_arc_data = dict(
                    type = 'FeatureCollection',
                    features = features_data
                    )
    
    return json_arc_data

with open(_export_dir+'arc_flows_data.json','w') as json_arc_data:
    json.dump(json_flows_file(voronoi_gpd, edges_pd), json_arc_data)
    
    