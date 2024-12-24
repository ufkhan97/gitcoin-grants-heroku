import streamlit as st
import pandas as pd
import psycopg2 as pg
import os
from typing import Union, Dict, List, Any
from datetime import datetime, timezone
import requests
import re


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

def parse_config_file(file_content):
    """Parse the config file content and extract token information."""
    data = []
    chain_pattern = re.compile(r'{\s*id:\s*(\d+),\s*name:\s*"([^"]+)",.*?tokens:\s*\[(.*?)\].*?}', re.DOTALL)
    token_pattern = re.compile(r'code:\s*"(?P<code>[^"]+)".*?address:\s*"(?P<address>[^"]+)".*?decimals:\s*(?P<decimals>\d+).*?priceSource:\s*{\s*chainId:\s*(?P<price_source_chain_id>\d+).*?address:\s*"(?P<price_source_address>[^"]+)"', re.DOTALL)
    chain_matches = chain_pattern.findall(file_content)

    for chain_match in chain_matches:
        chain_id = int(chain_match[0])
        chain_name = chain_match[1]
        token_data = chain_match[2]

        token_matches = token_pattern.finditer(token_data)

        for token_match in token_matches:
            token_code = token_match.group('code')
            token_address = token_match.group('address')
            token_decimals = int(token_match.group('decimals'))
            price_source_chain_id = int(token_match.group('price_source_chain_id'))
            price_source_address = token_match.group('price_source_address')

            data.append([
                chain_id,
                chain_name,
                token_code,
                token_address,
                token_decimals,
                price_source_chain_id,
                price_source_address
            ])

    if data:
        columns = [
            'chain_id',
            'chain_name',
            'token_code',
            'token_address',
            'token_decimals',
            'price_source_chain_id',
            'price_source_address'
        ]
        df = pd.DataFrame(data, columns=columns)
        df['token_address'] = df['token_address'].str.lower()
        df['price_source_address'] = df['price_source_address'].str.lower()
        return df
    else:
        print("No token data found in the file.")
        return None
    
@st.cache_resource(ttl=36000) #10 hours
def fetch_tokens_config():
    """Fetch and parse the token configuration from the GitHub repository."""
    url = 'https://raw.githubusercontent.com/gitcoinco/grants-stack-indexer/main/src/config.ts'
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
    except requests.RequestException as e:
        print(f"Failed to fetch data from {url}. Error: {e}")
        return None

    df = parse_config_file(response.text)
    return df


@st.cache_resource(ttl=time_to_live)
def get_voters_by_project(round_chain_pairs):
    if not round_chain_pairs:
        st.error("No round_chain_pairs provided.")
        return pd.DataFrame()  # Return an empty DataFrame if no pairs are provided

    # Prepare the round_chain_pairs for the SQL query
    round_ids = ', '.join(f"'{pair[0]}'" for pair in round_chain_pairs)
    chain_ids = ', '.join(f"'{pair[1]}'" for pair in round_chain_pairs)

    # Construct the SQL query with the formatted pairs
    query = f"""
    WITH round_chain_pairs AS (
        SELECT 
            unnest(ARRAY[{round_ids}]::text[]) AS round_id,
            unnest(ARRAY[{chain_ids}]::text[]) AS chain_id
    )
    SELECT
        (a.metadata->'application'->'project'->>'title') AS "project_name",
        d.donor_address AS "voter",
        coalesce(ens.name, d.donor_address) AS "voter_id",
        sum(d.amount_in_usd) AS "amountUSD"
    FROM
        public.donations d
    JOIN round_chain_pairs rcp 
        ON d.round_id::text = rcp.round_id 
        AND d.chain_id::text = rcp.chain_id
    LEFT JOIN public.applications a 
        ON a.round_id = d.round_id 
        AND a.id = d.application_id 
        AND a.chain_id = d.chain_id
    LEFT JOIN   "experimental_views"."ens_names_allo_donors_20241022231136" ens
        ON d.donor_address = ens.address
    GROUP BY 1, 2, 3
    ORDER BY 4 desc 
    """

    return run_query(query, database='grants', is_file=False)

@st.cache_resource(ttl=time_to_live)
def get_projects(round_chain_pairs):
    if not round_chain_pairs:
        st.error("No round_chain_pairs provided.")
        return pd.DataFrame()  # Return an empty DataFrame if no pairs are provided

    # Prepare the round_chain_pairs for the SQL query
    round_ids = ', '.join(f"'{pair[0]}'" for pair in round_chain_pairs)
    chain_ids = ', '.join(f"'{pair[1]}'" for pair in round_chain_pairs)

    # Construct the SQL query with the formatted pairs
    query = f"""
    WITH round_chain_pairs AS (
        SELECT 
            unnest(ARRAY[{round_ids}]::text[]) AS round_id,
            unnest(ARRAY[{chain_ids}]::text[]) AS chain_id
    )
    SELECT 
        a.id AS application_id,
        (a.metadata->'application'->'project'->>'title') AS title,
        (a.metadata->'application'->>'recipient') AS recipient_address,
        (r."round_metadata" #>> '{{name}}')::text AS "round_name",
        a.chain_id::text,
        a.round_id::text,
        a.project_id AS "projectId",
        a.status,
        a.total_donations_count AS votes,
        a.total_amount_donated_in_usd AS "amountUSD",
        a.unique_donors_count
    FROM 
        public.applications AS a
    LEFT JOIN rounds r ON a.round_id = r.id AND a.chain_id = r.chain_id
    JOIN 
        round_chain_pairs rcp 
        ON a.round_id::text = rcp.round_id 
        AND a.chain_id::text = rcp.chain_id
    WHERE 
        a.status = 'APPROVED';
    """

    return run_query(query, database='grants', is_file=False)

def get_unique_donors(round_chain_pairs):
    round_ids = ', '.join(f"'{pair[0]}'" for pair in round_chain_pairs)
    chain_ids = ', '.join(f"'{pair[1]}'" for pair in round_chain_pairs)

    query = f"""
    WITH round_chain_pairs AS (
        SELECT 
            unnest(ARRAY[{round_ids}]::text[]) AS round_id,
            unnest(ARRAY[{chain_ids}]::text[]) AS chain_id
    )
    SELECT 
        count(distinct donor_address)
    FROM 
        public.donations AS d
    JOIN 
        round_chain_pairs rcp 
        ON d.round_id::text = rcp.round_id 
        AND d.chain_id::text = rcp.chain_id
    """
    return run_query(query, database='grants', is_file=False)

def get_hourly_contributions(round_chain_pairs):
    round_ids = ', '.join([f"'{pair[0]}'" for pair in round_chain_pairs])
    chain_ids = ', '.join([f"'{pair[1]}'" for pair in round_chain_pairs])

    query = f"""
    WITH round_chain_pairs AS (
        SELECT 
            unnest(ARRAY[{round_ids}]::text[]) AS round_id,
            unnest(ARRAY[{chain_ids}]::text[]) AS chain_id
    )
    SELECT 
        date_trunc('hour', timestamp) AS hour,
        d.chain_id,
        d.round_id,
        token_address,
        SUM(amount_in_usd) AS total_amount
    FROM 
        public.donations AS d
    JOIN 
        round_chain_pairs rcp 
        ON d.round_id::text = rcp.round_id 
        AND d.chain_id::text = rcp.chain_id
    GROUP BY 1, 2, 3, 4
    ORDER BY 1, 2, 3, 4
    """

    token_map = fetch_tokens_config()
    token_map = token_map[['chain_id', 'token_address', 'token_code']]
    token_map['token_address'] = token_map['token_address'].str.lower()

    dfh = run_query(query, database='grants', is_file=False)
    dfh = pd.merge(dfh, token_map, how='left', left_on=['chain_id', 'token_address'], right_on=['chain_id', 'token_address'])
    return dfh



def get_round_data():
    return run_query(
        "queries/get_rounds.sql",
        database="grants",
        is_file=True
    )

@st.cache_resource(ttl=time_to_live)
def get_2024_stats():
    return run_query(
        "queries/get_2024_stats.sql",
        database="grants",
        is_file=True
    )

def add_round_options(dfr):
    dfr['options'] = dfr['round_name'] + ' | ' + dfr['type'].str.capitalize() + ' Round'
    dfr['type'] = pd.Categorical(dfr['type'], categories=['program', 'ecosystem'], ordered=True)
    dfr = dfr.sort_values(by=['type', 'round_name'])
    return dfr


@st.cache_resource(ttl=time_to_live)
def load_round_data(program, dfr):
    dfr = dfr[dfr['program'] == program]
    # Create list of (round_id, chain_id) pairs
    round_chain_pairs = [
        (str(row['round_id']).lower(), str(row['chain_id'])) 
        for _, row in dfr.iterrows()
    ]
    unique_donors = get_unique_donors(round_chain_pairs)
    hourly_contributions = get_hourly_contributions(round_chain_pairs)
    dfp = get_projects(round_chain_pairs)
    dfr = add_round_options(dfr)
    st.session_state.dfp = dfp
    st.session_state.dfr = dfr
    st.session_state.unique_donors = unique_donors
    st.session_state.hourly_contributions = hourly_contributions
    st.session_state.data_loaded = True

    return dfp, dfr, unique_donors, hourly_contributions

def get_time_left(target_time):
    now = datetime.now(timezone.utc)
    time_diff = target_time - now
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if time_diff.days < 0:
        return f"0 days   0 hours   0 minutes"
    return f"{time_diff.days} days   {hours} hours   {minutes} minutes"

