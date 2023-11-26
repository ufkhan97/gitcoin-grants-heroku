import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone


BASE_URL = "https://indexer-production.fly.dev/data"
time_to_live = 3600  # 60 minutes

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

def get_chain_block_range(dfv):
    chain_ids_blocks_range = dfv.groupby('chain_id')['blockNumber'].agg(['min', 'max']).reset_index()
    chain_ids_blocks_range['min'] = chain_ids_blocks_range['min'].astype(int)
    chain_ids_blocks_range['max'] = chain_ids_blocks_range['max'].astype(int)
    return chain_ids_blocks_range.values.tolist()

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


@st.cache_resource(ttl=time_to_live)
def load_round_data(program, csv_path='all_rounds.csv'):
    round_data = pd.read_csv(csv_path)
    round_data = round_data[round_data['program'] == program]

    dfv_list = []
    dfp_list = []

    for _, row in round_data.iterrows():
        raw_projects_data = load_data(str(row['chain_id']), str(row['round_id']), "applications")
        projects_list = transform_projects_data(raw_projects_data)
        dfp = pd.DataFrame(projects_list)
        dfv = pd.DataFrame(load_data(str(row['chain_id']), str(row['round_id']), "votes"))

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
    dfv = pd.merge(dfv, token_map, how='left', left_on=['chain_id','token'], right_on=['chain_id','token'])

    chain_starting_blocks = dfv.groupby('chain_id')['blockNumber'].min().to_dict()
    starting_time = pd.to_datetime(round_data['starting_time'].min())
    chain_block_range = get_chain_block_range(dfv)
    df_times = generate_block_timestamps(chain_block_range, starting_time)
    df_times = df_times[df_times['block_timestamp'] >= starting_time]
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

