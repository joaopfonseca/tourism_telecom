# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

from config import _export_dir

def preprocess(df, df2, df3, new_node_ids):
    
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
    dataframe = df_final[['user_id','date_time','user_origin','cell_id', 'cellid2']]#'latitude','longitude', 'cellid2']]
    
    new_node_ids['latitude'] = new_node_ids['lat']
    new_node_ids['longitude'] = new_node_ids['lon']
    
    refs = new_node_ids[['cellid', 'cellid2', 'longitude', 'latitude']]
    
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
    
    #df_merged.to_csv(_export_dir+'CDR_events_preprocessed.csv', index=False)
    return df_merged


#df2 = pd.read_csv(_data_dir+'site_lookup_outubro.csv')
def preprocess_cells(df):
    def conditional_float_to_string(param):
        if np.isnan(param):
            new_param = 'none'
        else:
            new_param=str(int(param))
        return new_param

    new_keys2 = []
    for key in df.keys():
        new_key= key.replace('site_lookup_outubro.site_lookup_concelhos', '')
        new_keys2.append(new_key)
    df.columns = new_keys2
    df['longitude'] = df['centroide_longitude']
    df['latitude'] = df['centroide_latitude']
    df['cellid_df2'] = df['ci']
    df['real_cellid'] = df['cellid_df2'].apply(conditional_float_to_string) + df['lac'].apply(conditional_float_to_string) + df['protocol_'].apply(conditional_float_to_string)
    df['real_cellid'] = df['real_cellid'].astype(str)
    
    df['cell_id'] = df['real_cellid']
    
    return df[['cell_id','longitude','latitude', 'name_site' ,'concelho', 'real_cellid']]













