import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone
import plotly.graph_objs as go
import plotly.express as px
import locale
import time
import networkx as nx
import utils

st.set_page_config(
    page_title="Data - Gitcoin Grants",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

## DEPLOYED ON HEROKU 
# https://gitcoin-grants-51f2c0c12a8e.herokuapp.com/


st.image('657c7ed16b14af693c08b92d_GTC-Logotype-Dark.png', width = 300)
st.write('')
st.write('This page highlights some of the key metrics and insights from the recent Gitcoin Grants Programs. Select a program below to get started!')

program_data = pd.read_csv("all_rounds.csv")
program_option = st.selectbox( 'Select Program', program_data['program'].unique())
st.title(program_option + ' Summary')

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

def create_token_comparison_bar_chart(dfv):
    # Group by token_symbol and sum the amountUSD
    grouped_data = dfv.groupby('token_symbol')['amountUSD'].sum().reset_index()
    # Calculate the total amountUSD for percentage calculation
    total_amountUSD = grouped_data['amountUSD'].sum()
    # Calculate the percentage for each token
    grouped_data['percentage'] = (grouped_data['amountUSD'] / total_amountUSD) 
    # Create the bar chart with renamed axes and title
    fig = px.bar(grouped_data, x='token_symbol', y='amountUSD', 
                 title='Contributions (in USD) by Token', 
                 labels={'token_symbol': 'Token', 'amountUSD': 'Contribution (USD)'})
    # Update hover template to display clean USD numbers
    fig.update_traces(hovertemplate='Token: %{x}<br>Contribution: $%{y:,.2f}')
    fig.update_yaxes(tickprefix="$", tickformat="2s")
    # Add percentage as labels on the bars
    fig.update_traces(texttemplate='%{customdata:.2%}', textposition='outside', customdata=grouped_data['percentage'])
    # Add padding at the top of the function for the texttemplate and increase the text size
    fig.update_layout(
        autosize=False,
        height=600,
        margin=dict(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=10
        ),
        font=dict(
            size=14,
        )
    )
    return fig

def get_USD_by_round_chart(dfp, color_map):
    grouped_data = dfp.groupby('round_name')['amountUSD'].sum().reset_index().sort_values('amountUSD', ascending=False)
    fig = px.bar(grouped_data, y='round_name', x='amountUSD', title='Crowdfunded (in USD) by Round', 
                 color='round_name', labels={'amountUSD': 'Crowdfunded Amount (USD)', 'round_name': 'Round Name'}, 
                 color_discrete_map=color_map, orientation='h')
    fig.update_traces(hovertemplate='Amount: $%{x:,.2f}', texttemplate='$%{x:,.3s}', textposition='auto')
    fig.update_layout(showlegend=False, height=600)  # Expanded height
    fig.update_xaxes(tickprefix="$", tickformat="2s")
    return fig

def get_contributions_by_round_chart(dfp, color_map):
    grouped_data = dfp.groupby('round_name')['votes'].sum().reset_index().sort_values('votes', ascending=False)
    fig = px.bar(grouped_data, y='round_name', x='votes', title='Total Contributions (#) by Round', 
                 color='round_name', labels={'votes': 'Number of Contributions', 'round_name': 'Round Name'}, 
                 color_discrete_map=color_map, orientation='h')
    fig.update_traces(hovertemplate='Number of Contributions: %{x:,.2f}', texttemplate='%{x:,.3s}', textposition='auto')
    fig.update_layout(showlegend=False, height=600)  # Expanded height
    fig.update_xaxes(tickprefix="", tickformat="2s")
    return fig

def get_contribution_time_series_chart(dfv):
    dfv_count = dfv.groupby([dfv['block_timestamp'].dt.strftime('%m-%d-%Y %H')])['id'].nunique()
    dfv_count.index = pd.to_datetime(dfv_count.index)
    dfv_count = dfv_count.reindex(pd.date_range(start=dfv_count.index.min(), end=dfv_count.index.max(), freq='H'), fill_value=0)
    fig = px.bar(dfv_count, x=dfv_count.index, y='id', labels={'id': 'Number of Contributions', 'index': 'Time'}, title='Hourly Contributions over Time')
    fig.update_layout()
    return fig 

def get_cumulative_amountUSD_time_series_chart(dfv):
    dfv_cumulative = dfv.groupby([dfv['block_timestamp']])['amountUSD'].sum().cumsum()
    dfv_cumulative.index = pd.to_datetime(dfv_cumulative.index)
    fig = px.area(dfv_cumulative, x=dfv_cumulative.index, y='amountUSD', labels={'amountUSD': 'Total Donations (USD)', 'block_timestamp': 'Time'}, title='Total Donations Over Time (USD)')
    fig.update_layout()
    fig.update_yaxes(tickprefix="$", tickformat="2s")
    return fig

def create_treemap(dfp):
    dfp['shortened_title'] = dfp['title'].apply(lambda x: x[:15] + '...' if len(x) > 20 else x)
    fig = px.treemap(dfp, path=['shortened_title'], values='amountUSD', hover_data=['title', 'amountUSD'])
    # Update hovertemplate to format the hover information
    fig.update_traces(
        texttemplate='%{label}<br>$%{value:.3s}',
        hovertemplate='<b>%{customdata[0]}</b><br>Amount: $%{customdata[1]:,.2f}',
        textposition='middle center',
        textfont_size=20
    )
    fig.update_traces(texttemplate='%{label}<br>$%{value:.3s}', textposition='middle center', textfont_size=20)
    fig.update_layout(font=dict(size=20))
    fig.update_layout(height=550)
    fig.update_layout(title_text="Donations by Grant")
    
    return fig





col1, col2 = st.columns(2)
col1.metric('Matching Pool', '${:,.2f}'.format(round_data['matching_pool'].sum()))
col1.metric('Total Donated', '${:,.2f}'.format(dfp['amountUSD'].sum()))
col1.metric("Total Donations", '{:,.0f}'.format(dfp['votes'].sum()))
col1.metric('Unique Donors', '{:,.0f}'.format(dfv['voter'].nunique()))
col1.metric('Total Rounds', '{:,.0f}'.format(round_data['round_id'].nunique()))
col1.metric('Total Projects', '{:,.0f}'.format(len(dfp)))

if program_option == 'GG20':
    time_left = utils.get_time_left(pd.to_datetime('2024-05-07 23:59:59', utc=True))
    col2.subheader('🕰 Time Left ')
    col2.subheader(time_left)
    
col2.plotly_chart(get_cumulative_amountUSD_time_series_chart(dfv), use_container_width=True)
#st.plotly_chart(get_contribution_time_series_chart(dfv), use_container_width=True) 


if dfp['round_id'].nunique() > 1:
    color_map = dict(zip(dfp['round_name'].unique(), px.colors.qualitative.Pastel))
    col1, col2 = st.columns(2)
    col1.plotly_chart(create_token_comparison_bar_chart(dfv), use_container_width=True)
    col2.plotly_chart(get_USD_by_round_chart(dfp, color_map), use_container_width=True)
    
    st.title("Round Details")
    # selectbox to select the round
    option = st.selectbox(
        'Select Round',
        round_data['options'].unique())
    option = option.split(' - ')[0]
    dfv = dfv[dfv['round_name'] == option]
    dfp = dfp[dfp['round_name'] == option]
    round_data = round_data[round_data['round_name'] == option]
    dfp['votes'] = dfp['votes'].astype(int)
    dfp['amountUSD'] = dfp['amountUSD'].astype(float)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('Matching Pool', '${:,.0f}'.format(round_data['matching_pool'].sum()))
    col2.metric('Total Donated', '${:,.0f}'.format(dfp['amountUSD'].sum()))
    col3.metric('Total Donations',  '{:,.0f}'.format(dfp['votes'].sum()))
    col4.metric('Total Projects',  '{:,.0f}'.format(len(dfp)))
    col5.metric('Unique Donors',  '{:,.0f}'.format(dfv['voter'].nunique()))

st.plotly_chart(create_treemap(dfp.copy()), use_container_width=True)

#df = pd.merge(dfv, dfp[['projectId', 'title']], how='left', left_on='projectId', right_on='projectId')

st.write('## Grants Leaderboard')
dfp['Project Link'] = 'https://explorer.gitcoin.co/#/round/' + dfp['chain_id'].astype(str) +'/' + dfp['round_id'].astype(str) + '/' + dfp['id'].astype(str)
df_display = dfp[['title', 'unique_donors_count', 'amountUSD', 'Project Link']].sort_values('unique_donors_count', ascending=False)
df_display.columns = ['Title', 'Donors', '$ Amount (USD)', 'Project Link']
df_display['$ Amount (USD)'] = df_display['$ Amount (USD)'].round(2)
df_display = df_display.reset_index(drop=True)
df_display['Title'] = df_display.apply(lambda row: f'<a href="{row["Project Link"]}">{row["Title"]}</a>', axis=1)
df_display = df_display.drop(columns=['Project Link'])
df_html = df_display.to_html(escape=False, index=False)
st.write(df_html, unsafe_allow_html=True)


