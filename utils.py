import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone
import psycopg2 as pg
import os
from dune_client.client import DuneClient


from dotenv import load_dotenv
load_dotenv()  # This loads the variables from .env

# Now you can use os.getenv to access your variables
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

dune_api_key = os.environ['DUNE_API_KEY']

blockchain_mapping = {
        1: "ethereum",
        10: "optimism",
        137: "polygon",
        250: "fantom",
        324: "zksync",
        8453: "base",
        42161: "arbitrum",
        43114: "avalanche_c",
        534352: "scroll"
    }

BASE_URL = "https://indexer-production.fly.dev/data"
time_to_live = 900  # 15 minutes

def run_query(query, db):
    """Run query and return results"""
    if db == 'grants':
        db_host = grants_db_host
        db_port = grants_db_port
        db_name = grants_db_name
        db_username = grants_db_username
        db_password = grants_db_password
    elif db == 'indexer':
        db_host = indexer_db_host
        db_port = indexer_db_port
        db_name = indexer_db_name
        db_username = indexer_db_username
        db_password = indexer_db_password
    try:
        conn = pg.connect(host=db_host, port=db_port, dbname=db_name, user=db_username, password=db_password)
        cur = conn.cursor()
        cur.execute(query)
        col_names = [desc[0] for desc in cur.description]
        results = pd.DataFrame(cur.fetchall(), columns=col_names)
    except pg.Error as e:
        st.warning(f"ERROR: Could not execute the query. {e}")
    finally:
        conn.close()
    return results

@st.cache_resource(ttl=time_to_live)
def run_query_from_file(filename, db='grants'):
    try:
        with open(filename, 'r') as f:
            query = f.read()
    except IOError:
        print(f"Error: File {filename} not found or not readable.")
        return None
    try:
        return run_query(query, db)
    except Exception as e:
        print(f"Error: Failed to execute query. {e}")
        return None
    
@st.cache_resource(ttl=time_to_live)
def get_round_votes(round_id_list, chain_id):
    sql_query_file = 'queries/get_votes.sql'
    with open(sql_query_file, 'r') as file:
        query = file.read()
    query = query.format(round_id_list=round_id_list, chain_id=chain_id)
    results = run_query(query, 'indexer')
    return results

@st.cache_resource(ttl=time_to_live)
def get_round_projects(round_id_list, chain_id):
    sql_query_file = 'queries/get_projects.sql'
    with open(sql_query_file, 'r') as file:
        query = file.read()
    query = query.format(round_id_list=round_id_list, chain_id=chain_id)
    results = run_query(query, 'indexer')
    return results

# Helper function to load data from URLs
def safe_get(data, *keys):
    """Safely retrieve nested dictionary keys."""
    temp = data
    for key in keys:
        if isinstance(temp, dict) and key in temp:
            temp = temp[key]
        else:
            return None
    return temp


@st.cache_resource(ttl=time_to_live)
def load_data_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data from {url}. Error: {e}") ### Suppressing warnings from being public on streamlit
        return []

@st.cache_resource(ttl=time_to_live)
def load_data(chain_id, round_id, data_type):
    url = f"{BASE_URL}/{chain_id}/rounds/{round_id}/{data_type}.json"
    return load_data_from_url(url)

def transform_projects_data(data):
    projects = []
    for project in data:
        title = safe_get(project, 'metadata', 'application', 'project', 'title')
        grantAddress = safe_get(project, 'metadata', 'application', 'recipient')
        description = safe_get(project, 'metadata', 'application', 'project', 'description')
        
        if title and grantAddress:  # Ensure required fields are available
            project_data = {
                'projectId': project['projectId'],
                'title': title,
                'grantAddress': grantAddress,
                'status': project['status'],
                'amountUSD': project['amountUSD'],
                'votes': project['votes'],
                'uniqueContributors': project['uniqueContributors'],
                'description': description
            }
            projects.append(project_data)
    return projects

@st.cache_resource(ttl=time_to_live)
def load_passport_data():
    url = f"{BASE_URL}/passport_scores.json"
    data = load_data_from_url(url)
    
    passports = []
    for passport in data:
        address = passport.get('address')
        last_score_timestamp = passport.get('last_score_timestamp')
        status = passport.get('status')
        rawScore = safe_get(passport, 'evidence', 'rawScore') or 0

        if address:  # Ensure the required field is available
            passport_data = {
                'address': address,
                'last_score_timestamp': last_score_timestamp,
                'status': status,
                'rawScore': rawScore
            }
            passports.append(passport_data)

    df = pd.DataFrame(passports)
    if not df.empty:
        df['rawScore'] = df['rawScore'].astype(float)
    #df['last_score_timestamp'] = pd.to_datetime(df['last_score_timestamp'])
    return df

def get_chain_block_range(chain_id, dfv):
    dfv = dfv[dfv['chain_id'] == chain_id]
    min_block = dfv['blockNumber'].min()
    max_block = dfv['blockNumber'].max()
    return min_block, max_block

def generate_block_timestamps(chain_ids_blocks_range,round_starting_time):
    # Create an empty DataFrame for the results
    result_df = pd.DataFrame(columns=['chain_id', 'block_number', 'block_timestamp'])
    dataframe = pd.read_csv('chain_blocktimes.csv')
    for chain_id, min_block, max_block in chain_ids_blocks_range:
        chain_data = dataframe[dataframe['chainId'] == chain_id].iloc[0]
        if not chain_data.empty:
            # Calculate the average time per block
            total_time = pd.to_datetime(chain_data['max_time']) - pd.to_datetime(chain_data['min_time'])
            total_blocks = chain_data['max_block'] - chain_data['min_block']
            avg_time_per_block = total_time / total_blocks
            # Generate block numbers within the range
            block_numbers = np.arange( min_block,
                                       max_block + 1,
                                      1)
            # Generate timestamps
            start_time = pd.to_datetime(chain_data['min_time']) + avg_time_per_block * (min_block - chain_data['min_block'])
            timestamps = pd.date_range(start=start_time, periods=len(block_numbers), freq=avg_time_per_block)
            # Create a temporary DataFrame and append to the result
            temp_df = pd.DataFrame({'chain_id': chain_id,
                                    'block_number': block_numbers,
                                    'block_timestamp': timestamps})
            #temp_df = temp_df[temp_df['block_timestamp'] >= round_starting_time]
            result_df = pd.concat([result_df, temp_df], ignore_index=True)
    return result_df

def add_round_options(round_data):
    round_data['options'] = round_data['round_name'] + ' - ' + round_data['type'].str.capitalize() + ' Round'
    return round_data

def get_blocktime_from_dune(chain, min_block, max_block):
    sql_query_file = 'queries/get_blocktimes.sql'
    with open(sql_query_file, 'r') as file:
            query = file.read()
    query = query.format(chain=chain, min_block=min_block, max_block=max_block)
    client = DuneClient(api_key=dune_api_key)
    results = client.run_sql(
        query_sql=query, 
        performance='large')
    data = results.result.rows
    df = pd.DataFrame(data)
    return df

@st.cache_resource(ttl=time_to_live)
def load_round_data(program, csv_path='all_rounds.csv'):
    round_data = pd.read_csv(csv_path)
    round_data = round_data[round_data['program'] == program]

    dfv_list = []
    dfp_list = []

    for _, row in round_data.iterrows():
        round_id_list = "('" + str(row['round_id']).lower() + "')"

        dfp = get_round_projects(round_id_list, row['chain_id'])

        dfv = get_round_votes(round_id_list, row['chain_id'])

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


    token_map = pd.read_csv('token_map.csv')
    token_map['token'] = token_map['token'].str.lower()
    dfv = pd.merge(dfv, token_map, how='left', left_on=['chain_id','token'], right_on=['chain_id','token'])

    df_times = pd.DataFrame()
    for chain_id in dfv['chain_id'].unique():
        chain = blockchain_mapping.get(chain_id)
        min_block, max_block = get_chain_block_range(chain_id, dfv)
        df_times_temp = get_blocktime_from_dune(chain, min_block, max_block)
        df_times_temp['chain_id'] = chain_id
        df_times = pd.concat([df_times, df_times_temp], ignore_index=True)
    df_times['block_timestamp'] = pd.to_datetime(df_times['block_timestamp'])
    dfv = pd.merge(dfv, df_times, how='left', left_on=['chain_id', 'blockNumber'], right_on=['chain_id', 'block_number'])
    dfv['voter'] = dfv['voter'].str.lower()
    dfv = pd.merge(dfv, dfp[['projectId', 'title']], how='left', left_on='projectId', right_on='projectId')
    
    #dfv['rawScore'] = 0
    #dfpp = load_passport_data()
    #if not dfpp.empty:
    #    dfpp['address'] = dfpp['address'].str.lower()
    #    dfv = pd.merge(dfv, dfpp[['address', 'rawScore']], how='left', left_on='voter', right_on='address')
    
   # del dfpp
    df_ens = pd.read_csv('ens.csv')
    df_ens['address'] = df_ens['address'].str.lower()
    
    dfv = pd.merge(dfv, df_ens, how='left', left_on='voter', right_on='address')
    dfv['voter_id'] = dfv['name'].fillna(dfv['voter'])
    # drop duplicates
    dfv = dfv.drop_duplicates()
    round_data = add_round_options(round_data)
    st.session_state.dfv = dfv
    st.session_state.dfp = dfp
    st.session_state.round_data = round_data
    st.session_state.data_loaded = True

    return dfv, dfp, round_data

def get_time_left(target_time):
    now = datetime.now(timezone.utc)
    time_diff = target_time - now
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if time_diff.days < 0:
        return f"0 days   0 hours   0 minutes"
    return f"{time_diff.days} days   {hours} hours   {minutes} minutes"


