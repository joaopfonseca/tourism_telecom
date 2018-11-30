#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from config import constants, _export_dir, _data_dir



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

