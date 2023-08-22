import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime
import plotly.graph_objs as go
import plotly.express as px
import locale
import time
import networkx as nx
import utils

st.set_page_config(
    page_title="Gitcoin Grants Round 18",
    page_icon="📊",
    layout="wide",

)

## DEPLOYED ON HEROKU 
# https://gitcoin-grants-51f2c0c12a8e.herokuapp.com/

st.title('📊 Gitcoin Grants 18')
st.write('The Gitcoin Grants Program is a quarterly initiative that empowers everyday believers to drive funding toward what they believe matters, with the impact of individual donations being magnified by the use of the [Quadratic Funding (QF)](https://wtfisqf.com) distribution mechanism.')
st.write('You can donate to projects in the Round from August 15th 2023 12:00 UTC to August 29th 2023 12:00 UTC.')
st.write('👉 Visit [grants.gitcoin.co](https://grants.gitcoin.co) to donate.')



if "data_loaded" in st.session_state and st.session_state.data_loaded:
    dfv = st.session_state.dfv
    dfp = st.session_state.dfp
    round_data = st.session_state.round_data
else:
    data_load_state = st.text('Loading data...')
    dfv, dfp, round_data = utils.load_round_data()
    data_load_state.text("")



def create_token_comparison_pie_chart(dfv):
    # Group by token_symbol and sum the amountUSD
    grouped_data = dfv.groupby('token_symbol')['amountUSD'].sum().reset_index()
    fig = px.pie(grouped_data, names='token_symbol', values='amountUSD', title='ETH vs DAI Contributions (in $)', hole=0.3)
    for trace in fig.data:
        trace.hoverinfo = 'none'
    return fig

def get_USD_by_round_chart(dfp, color_map):
    grouped_data = dfp.groupby('round_name')['amountUSD'].sum().reset_index().sort_values('amountUSD', ascending=False)
    fig = px.bar(grouped_data, x='round_name', y='amountUSD', title='Crowdfunded (in $) by Round', 
                 color='round_name', labels={'amountUSD': 'Crowdfunded Amount ($)', 'round_name': 'Round Name'}, 
                 color_discrete_map=color_map)
    fig.update_layout(showlegend=False)
    return fig

def get_contributions_by_round_chart(dfp, color_map):
    grouped_data = dfp.groupby('round_name')['votes'].sum().reset_index().sort_values('votes', ascending=False)
    fig = px.bar(grouped_data, x='round_name', y='votes', title='Total Contributions (#) by Round', 
                 color='round_name', labels={'votes': 'Number of Contributions', 'round_name': 'Round Name'}, 
                 color_discrete_map=color_map)
    fig.update_layout(showlegend=False)
    return fig

def get_contribution_time_series_chart(dfv):
    dfv_count = dfv.groupby([dfv['timestamp'].dt.strftime('%m-%d-%Y %H')])['id'].nunique()
    dfv_count.index = pd.to_datetime(dfv_count.index)
    dfv_count = dfv_count.reindex(pd.date_range(start=dfv_count.index.min(), end=dfv_count.index.max(), freq='H'), fill_value=0)
    fig = px.bar(dfv_count, x=dfv_count.index, y='id', labels={'id': 'Number of Contributions', 'index': 'Time'}, title='Number of Contributions over Time')
    fig.update_layout()
    return fig 


st.subheader('Rounds Summary')

col1, col2 = st.columns(2)
col1.metric('Matching Pool', '${:,.2f}'.format(round_data['matching_pool'].sum()))
col1.metric('Total Donated', '${:,.2f}'.format(dfp['amountUSD'].sum()))
col1.metric("Total Donations", '{:,.0f}'.format(dfp['votes'].sum()))
col1.metric('Unique Donors', '{:,.0f}'.format(dfv['voter'].nunique()))
col1.metric('Total Rounds', '{:,.0f}'.format(dfp['round_id'].nunique()))
col2.plotly_chart(create_token_comparison_pie_chart(dfv))

color_map = dict(zip(dfp['round_name'].unique(), px.colors.qualitative.Pastel))
col1, col2 = st.columns(2)
col1.plotly_chart(get_USD_by_round_chart(dfp, color_map))
col2.plotly_chart(get_contributions_by_round_chart(dfp, color_map))
st.plotly_chart(get_contribution_time_series_chart(dfv), use_container_width=True) 


st.title("Round Details")
# selectbox to select the round
option = st.selectbox(
    'Select Round',
    dfv['round_name'].unique())

dfv = dfv[dfv['round_name'] == option]
dfp = dfp[dfp['round_name'] == option]
round_data = round_data[round_data['round_name'] == option]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric('Matching Pool', '${:,.2f}'.format(round_data['matching_pool'].sum()))
col2.metric('Total Donated', '${:,.2f}'.format(dfp['amountUSD'].sum()))
col3.metric('Total Donations',  '{:,.0f}'.format(dfp['votes'].sum()))
col4.metric('Total Projects',  '{:,.0f}'.format(len(dfp)))
col5.metric('Unique Donors',  '{:,.0f}'.format(dfv['voter'].nunique()))

def create_treemap(dfp):
    fig = px.treemap(dfp, path=['title'], values='amountUSD', hover_data=['title'])
    fig.update_traces(texttemplate='%{label}<br>$%{value:.3s}', textposition='middle center', textfont_size=20)
    fig.update_layout(font=dict(size=20))
    fig.update_layout(height=540)
    return fig

st.plotly_chart(create_treemap(dfp.copy()), use_container_width=True)

df = pd.merge(dfv, dfp[['projectId', 'title']], how='left', left_on='projectId', right_on='projectId')

st.write('## Projects')
# write projects title, votes, amount USD, unique contributors
df_display = dfp[['title', 'votes',  'amountUSD',]].sort_values('votes', ascending=False)
df_display.columns = ['Title', 'Votes',  'Amount (USD)',]
df_display['Amount (USD)'] = df_display['Amount (USD)'].apply(lambda x: '${:,.2f}'.format(x))
df_display['Votes'] = df_display['Votes'].apply(lambda x: '{:,.0f}'.format(x))
df_display = df_display.reset_index(drop=True)
st.dataframe(df_display, use_container_width=True, height=500)

