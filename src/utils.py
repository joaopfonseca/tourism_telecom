#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from random import randint
import pandas as pd
import json



def generate_structured_flows(voronoi_gpd, edges_pd):
    """
    voronoi_gpd: geometry, centroid, cell_id
    edges_pd: from, to, total_people, date_time, weight
    """
    edges_pd['weight'] = edges_pd['total_people']
    #voronoi_gpd['cell_id']=voronoi_gpd['cellid_x']
    
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
    # getting data for voronoi cells
    features_data = []
    for cell in range(len(voronoi_gpd)):
        cell_id = voronoi_gpd['cell_id'][cell]
        geometry_coords = []
        for vertex in list(voronoi_gpd['geometry'][cell].exterior.coords):
            geometry_coords.append(list(vertex))
        
        
        
        geometry_data = dict(
                type = 'Feature',
                geometry = dict(
                        coordinates = [geometry_coords],
                        type = 'Polygon'
                        
                        ),
                properties = dict(
                        centroid = [voronoi_gpd['centroid'][cell].x, voronoi_gpd['centroid'][cell].y],
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



def export_flows_as_json(voronoi_gpd, edges_pd, json_file):
    """
    Useful for Deck.GL visualizations!
    """
    with open(json_file,'w') as file:
        json.dump(generate_structured_flows(voronoi_gpd, edges_pd), file)





