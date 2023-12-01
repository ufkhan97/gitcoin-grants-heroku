import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import utils 

st.set_page_config(
    page_title="Data - Gitcoin Leaderboard",
    page_icon="favicon.png",
    layout="wide",
)

st.title('💸 Projects and their donors')

st.write("This page gives you the list of donors for a particular project after you enter the grant address or the project id.The grant address or the projectid should have the same capitalization as is given in gitcoin")

grant = st.text_input('Enter grant address', 'none')
project_id = st.text_input('or Enter Project ID', 'none')

program_data = pd.read_csv("all_rounds.csv")
program_option = st.selectbox( 'Select Program', program_data['program'].unique())
st.title(program_option)


if "program_option" in st.session_state and st.session_state.program_option != program_option:
    st.session_state.data_loaded = False
st.session_state.program_option = program_option

if "data_loaded" in st.session_state and st.session_state.data_loaded:
    dfv = st.session_state.dfv
    dfp = st.session_state.dfp
    round_data = st.session_state.round_data
else:
    data_load_state = st.text('Loading data...')
    dfv, dfp, round_data = utils.load_round_data(program_option, "all_rounds.csv")
    data_load_state.text("")


if(project_id != 'none'):
    st.write("Loading - may take upto 2 minutes")
    filtered_data = dfv[dfv['projectId'] == project_id]
    required_columns = filtered_data[['voter_id', 'block_timestamp', 'token_symbol','amount','amountUSD', 'round_name']]
    st.dataframe(required_columns)

if(grant != 'none'):
    st.write("Loading - may take upto 2 minutes")
    filtered_data = dfv[dfv['grantAddress'] == grant]
    required_columns = filtered_data[['title','voter_id', 'block_timestamp', 'token_symbol','amount','amountUSD', 'round_name']]
    st.dataframe(required_columns)



