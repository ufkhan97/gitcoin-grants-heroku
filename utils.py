import streamlit as st
import pandas as pd
import psycopg2 as pg
import os
from typing import Union, Dict, List, Any
from datetime import datetime, timezone


try:
    from dotenv import load_dotenv
    if load_dotenv():
        print("Loaded .env file")
    else:
        print("No .env file found or loaded")
except ImportError:
    print("dotenv not installed, skipping .env file loading")

grants_db_host= os.environ['GRANTS_DB_HOST']
grants_db_port = os.environ['GRANTS_DB_PORT']
grants_db_name = os.environ['GRANTS_DB_NAME']
grants_db_username = os.environ['GRANTS_DB_USERNAME']
grants_db_password = os.environ['GRANTS_DB_PASSWORD']

indexer_db_host= os.environ['INDEXER_DB_HOST']
indexer_db_port = os.environ['INDEXER_DB_PORT']
indexer_db_name = os.environ['INDEXER_DB_NAME']
indexer_db_username = os.environ['INDEXER_DB_USERNAME']
indexer_db_password = os.environ['INDEXER_DB_PASSWORD']

time_to_live = 900  # 15 minutes

@st.cache_resource(ttl=time_to_live)  # 15 minutes cache
def run_query(query, params=None, database='grants', is_file=False):
    """
    Execute a SQL query and return the results as a DataFrame.
    
    :param query: SQL query string or filename containing the query
    :param params: Parameters for the SQL query (dict for named params, list for positional)
    :param database: Database to query ('grants' or 'indexer')
    :param is_file: Whether the query is a filename (True) or a SQL string (False)
    :return: DataFrame containing query results
    """
    if is_file:
        with open(query, 'r') as f:
            query = f.read()
    
    db_config = {
        'host': os.environ[f'{database.upper()}_DB_HOST'],
        'port': os.environ[f'{database.upper()}_DB_PORT'],
        'dbname': os.environ[f'{database.upper()}_DB_NAME'],
        'user': os.environ[f'{database.upper()}_DB_USERNAME'],
        'password': os.environ[f'{database.upper()}_DB_PASSWORD']
    }
    
    try:
        with pg.connect(**db_config) as conn:
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
        return df
    except pg.Error as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
    
@st.cache_resource(ttl=time_to_live)
def get_round_votes(round_id, chain_id):
    return run_query(
        "queries/get_votes.sql",
        {"round_id": round_id, "chain_id": chain_id},
        database="indexer",
        is_file=True
    )

@st.cache_resource(ttl=time_to_live)
def get_round_projects(round_id, chain_id):
    return run_query(
        "queries/get_projects.sql",
        {"round_id": round_id, "chain_id": chain_id},
        database="indexer",
        is_file=True
    )

def get_round_data():
    return run_query(
        "queries/get_rounds.sql",
        database="indexer",
        is_file=True
    )

@st.cache_resource(ttl=time_to_live)
def get_2024_stats():
    return run_query(
        "queries/2024_stats.sql",
        database="grants",
        is_file=True
    )

def add_round_options(dfr):
    dfr['options'] = dfr['round_name'] + ' - ' + dfr['type'].str.capitalize() + ' Round'
    dfr['type'] = pd.Categorical(dfr['type'], categories=['program', 'ecosystem'], ordered=True)
    dfr = dfr.sort_values(by=['type', 'round_name'])
    return dfr


@st.cache_resource(ttl=time_to_live)
def load_round_data(program, csv_path='data/all_rounds.csv'):
    round_data = pd.read_csv(csv_path)
    round_data = round_data[round_data['program'] == program]

    dfr = get_round_data()
    round_data = round_data[['program', 'type', 'round_number', 'round_id', 'chain_id']]
    dfr = pd.merge(dfr, round_data, on=['round_id', 'chain_id'], how='inner')
    st.write(dfr)
    dfv_list = []
    dfp_list = []

    for _, row in dfr.iterrows():
        round_id = str(row['round_id']).lower()
        dfp = get_round_projects(round_id, row['chain_id'])
        dfv = get_round_votes(round_id, row['chain_id'])
        dfp['round_id'] = row['round_id']
        dfp['chain_id'] = row['chain_id']
        dfp['round_name'] = row['round_name']
        dfv['round_id'] = row['round_id']
        dfv['chain_id'] = row['chain_id']
        dfv['round_name'] = row['round_name']
        dfv_list.append(dfv)
        dfp_list.append(dfp)

    dfv = pd.concat(dfv_list)
    dfp = pd.concat(dfp_list)
    dfp = dfp[dfp['status'] == 'APPROVED']


    token_map = pd.read_csv('data/token_map.csv')
    token_map['token'] = token_map['token'].str.lower()
    dfv = pd.merge(dfv, token_map, how='left', left_on=['chain_id','token'], right_on=['chain_id','token'])


    dfv['voter'] = dfv['voter'].str.lower()
    dfv = pd.merge(dfv, dfp[['projectId', 'title']], how='left', left_on='projectId', right_on='projectId')
    
    df_ens = pd.read_csv('data/ens.csv')
    df_ens['address'] = df_ens['address'].str.lower()
    
    dfv = pd.merge(dfv, df_ens, how='left', left_on='voter', right_on='address')
    dfv['voter_id'] = dfv['name'].fillna(dfv['voter'])
    # drop duplicates
    dfv = dfv.drop_duplicates()
    dfr = add_round_options(dfr)
    st.session_state.dfv = dfv
    st.session_state.dfp = dfp
    st.session_state.dfr = dfr
    st.session_state.round_data = round_data
    st.session_state.data_loaded = True

    return dfv, dfp,  dfr, round_data

def get_time_left(target_time):
    now = datetime.now(timezone.utc)
    time_diff = target_time - now
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if time_diff.days < 0:
        return f"0 days   0 hours   0 minutes"
    return f"{time_diff.days} days   {hours} hours   {minutes} minutes"


