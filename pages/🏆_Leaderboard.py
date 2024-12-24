import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import utils 

st.set_page_config(
    page_title="Data - Gitcoin Leaderboard",
    page_icon="assets/favicon.png",
    layout="wide",
)

st.title('🏆 Donor Leaderboard')
st.write("This leaderboard shows the top donors by amount donated, and number of unique grants donated to. It's one way to see who's been the most generous and who's been the most loving.")

dfr = utils.get_round_data()
program_option = st.selectbox('Select Program', dfr['program'].unique())
st.title(program_option)

if "program_option" in st.session_state and st.session_state.program_option != program_option:
    st.session_state.data_loaded = False
st.session_state.program_option = program_option

if "data_loaded" in st.session_state and st.session_state.data_loaded:
    dfp = st.session_state.dfp
    dfr = st.session_state.dfr
    unique_donors = st.session_state.unique_donors
    hourly_contributions = st.session_state.hourly_contributions
else:
    data_load_state = st.text('Loading data...')
    dfp, dfr, unique_donors, hourly_contributions = utils.load_round_data(program_option, dfr)
    data_load_state.text("")

# Get votes data for the selected program
round_chain_pairs = [
    (str(row['round_id']).lower(), str(row['chain_id'])) 
    for _, row in dfr.iterrows()
]
votes_by_voter_and_project = utils.get_voters_by_project(round_chain_pairs)

# Group by voter to get total donations and unique grants
dfv_grouped = votes_by_voter_and_project.groupby(['voter_id']).agg({
    'amountUSD': 'sum',
    'project_name': 'nunique'
}).reset_index()

dfv_grouped.columns = ['Voter ID', 'Amount USD', 'Unique Grants']
dfv_grouped = dfv_grouped.sort_values('Amount USD', ascending=False)
dfv_grouped['Amount USD'] = dfv_grouped['Amount USD'].apply(lambda x: "${:,.2f}".format(x))
dfv_grouped['Unique Grants'] = dfv_grouped['Unique Grants'].astype(int)

# For Most Generous ranking
# Convert Amount USD back to numeric by removing $ and , before sorting
dfv_generous = dfv_grouped.copy()
dfv_generous['Amount USD'] = dfv_generous['Amount USD'].str.replace('$', '').str.replace(',', '').astype(float)
dfv_generous = dfv_generous.sort_values('Amount USD', ascending=False)
dfv_generous['Amount USD'] = dfv_generous['Amount USD'].apply(lambda x: "${:,.2f}".format(x))
dfv_generous = dfv_generous[['Voter ID', 'Amount USD']].copy()
dfv_generous.insert(0, 'Rank', range(1, len(dfv_generous) + 1))

st.subheader('💸 Most Generous')
st.dataframe(dfv_generous.head(100), hide_index=True, use_container_width=True)

# For Most Loving ranking
dfv_loving = dfv_grouped.sort_values('Unique Grants', ascending=False)
dfv_loving = dfv_loving[['Voter ID', 'Unique Grants']].copy()
dfv_loving.insert(0, 'Rank', range(1, len(dfv_loving) + 1))

st.subheader('😘 Most Loving')
st.dataframe(dfv_loving.head(100), hide_index=True, use_container_width=True)