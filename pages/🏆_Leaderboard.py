import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import utils 
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

st.title('🏆 Donor Leaderboard')
st.write("This leaderboard shows the top donors by amount donated, and number of unique grants donated to. It's a great way to see who's been the most generous and who's been the most loving.")

dfv_grouped = dfv.groupby(['voter_id']).agg({'amountUSD': 'sum', 'grantAddress': 'nunique'}).reset_index()
dfv_grouped.columns = ['Voter ID', 'Amount USD', 'Unique Grants']
dfv_grouped = dfv_grouped.sort_values('Amount USD', ascending=False)
dfv_grouped['Amount USD'] = dfv_grouped['Amount USD'].apply(lambda x: "${:,.2f}".format(x))
dfv_grouped['Unique Grants'] = dfv_grouped['Unique Grants'].astype(int)
st.subheader('💸 Most Generous')
st.dataframe(dfv_grouped[['Voter ID','Amount USD']].reset_index(drop=True).head(100), width = 500)

dfv_grouped = dfv_grouped.sort_values('Unique Grants', ascending=False)
st.subheader('😘 Most Loving')
st.dataframe(dfv_grouped[['Voter ID','Unique Grants']].reset_index(drop=True).head(100), width=500)

#dfv_grouped = dfv_grouped.sort_values('Passport Score', ascending=False)
#st.subheader('🤝 Most Trustworthy')
#st.dataframe(dfv_grouped[['Voter ID','Passport Score']].reset_index(drop=True).head(100), width=500)