#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from config import constants, _export_dir, _data_dir


telecom_towers = pd.read_csv(_data_dir+'site_lookup_outubro.csv')

new_keys = []
for key in telecom_towers.keys():
    new_key= key.replace('site_lookup_outubro.site_lookup_concelhos', '')
    new_keys.append(new_key)
telecom_towers.columns = new_keys

ttdf = telecom_towers[['code_site','x_long','y_lat']].drop_duplicates('code_site')

attractions = pd.read_csv(_export_dir+'attractions.csv')

#missing: hotel locations, but why is it really necessary?
