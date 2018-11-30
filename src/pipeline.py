#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

from config import _export_dir, _data_dir
from events_preprocess import preprocess, preprocess_cells
from sna import get_dynamic_edgelist, generate_artificial_nodes
from utils import export_flows_as_json

"""
Scripts:
    config.py -> General configurations (utility purposes)
    sna.py -> Social Network Analysis functions.
    events_preprocess.py -> (Original) Cells and User activity preprocessing,
                            preprocessing of original data.
    
TODO:
    - Edit config.py file
    - Create functions for preliminary data visualization
"""

# =============================================================================
# preprocess cell/site data
# =============================================================================
print('Preprocessing cell/site data...')
cell_df = pd.read_csv(_data_dir+'site_lookup_outubro.csv')
cell_df = preprocess_cells(cell_df)
cell_df.to_csv(_export_dir+'CDR_cellsites_preprocessed.csv', index=False)

print('Generating nodes...')

artificial_nodes = generate_artificial_nodes(cell_df, 30000, 38.751296, -9.2180615)
new_node_ids = artificial_nodes['tower_cells_to_new_nodes']
voronoi = artificial_nodes['voronoi_cells']

# =============================================================================
# preprocess events data
# =============================================================================
print('Preprocessing events data...')
df = pd.read_csv(_data_dir+'union_all.csv')
df2 = cell_df.copy()
df3 = pd.read_csv(_data_dir+'mccmmc_optimized_new.csv')
new_node_ids
preprocessed_nodes = preprocess(df, df2, df3, new_node_ids) #table names/directories, and column names may need to be changed later on
preprocessed_nodes.to_csv(_export_dir+'CDR_events_preprocessed.csv', index=False)


# =============================================================================
#  create edge list
#  Visualization options will go here
# =============================================================================
print('Creating the edge list...')
dfna = pd.read_csv(_export_dir+'CDR_events_preprocessed.csv')
edge_list = get_dynamic_edgelist(dfna)
edge_list.to_csv(_export_dir+'edge_list.csv', index=False)


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

print('Creating nodes list...')
nodes = []
for row in range(len(cell_df)):
    node = (cell_df['cell_id'][row],cell_df['latitude'][row],cell_df['longitude'][row],cell_df['name_site'][row],cell_df['concelho'][row])
    nodes.append(node)

edge_list['weight'] = edge_list['total_people']

"""
At this point:
    - We have the edges and the nodes. From here many different visualizations can be made.

    - The the edges and nodes will be exported in json in order to serve as inputs for Deck.GL
visualizations.
"""

# =============================================================================
# Export output
# =============================================================================

print('Exporting output as json file...')
voronoi = voronoi.rename(index=str, columns={'geometry': 'geometry', 'cell_center': 'centroid', 'node_name': 'cell_id'})
# flows are faked
export_flows_as_json(voronoi, edge_list, _export_dir+'arc_flows_data.json')
new_node_ids[['cellid','cellid2']].to_csv(_export_dir+'nodes_anchors_association.csv', index=False)
print('Done!')







