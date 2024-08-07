import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import utils 

st.set_page_config(
    page_title="Data - Gitcoin Stats",
    page_icon="assets/favicon.png",
    layout="wide",
)
#st.image('657c7ed16b14af693c08b92d_GTC-Logotype-Dark.png', width = 300)
st.title('📈 Lifetime Stats')


st.write('')



cf = utils.run_query_from_file('queries/get_summary_stats.sql')
af = utils.get_2024_stats()
#st.write(cf)
#st.write(af)

last_updated = cf['last_donation'][0].strftime('%Y-%m-%d')

col1, col2, col3 = st.columns(3)
col1.metric(label="Funds Distributed", value='${:,.0f}'.format(cf['crowdfunded_usd'][0] + cf['matchingfunds'][0]  + af['crowdfunded_usd'][0] + af['matchingfunds'][0] + cf['bounties_distributed'][0] )) 
#col2.metric(label="Crowdfunding", value='${:,.0f}'.format(cf['crowdfunded_usd'][0] + af['crowdfunded_usd'][0]))
#col3.metric(label="Matching Funding", value='${:,.0f}'.format(cf['matchingfunds'][0] + af['matchingfunds'][0]))
#col1.metric(label="Total Unique Grants", value='{:,.0f}'.format(cf['unique_grantees'][0] + af['unique_grantees'][0]))
col3.metric(label="Total Donations", value='{:,.0f}'.format(cf['num_donations'][0] + af['num_donations'][0]) )
#col3.metric(label="Total Unique Voters", value='{:,.0f}'.format(cf['unique_voters'][0] + af['unique_voters'][0] ))
col2.metric(label="Number of Matching Pools Paid Out", value='{:,.0f}'.format(cf['num_rounds'][0] + af['num_rounds'][0]))

round_df = utils.run_query_from_file('queries/get_round_stats.sql')
#st.write(round_df)

# Filter round_df where round_num is not null
round_df = round_df[round_df['round_num'].notna()]

# Create a select box for the user to choose the y-axis column
# Filter out 'round_num' and 'last_donation' from the column list
round_df = round_df.rename(columns={
    'num_donations': 'Number of Donations',
    'round_num': 'Program Number',
    'unique_grantees': 'Unique Grantees',
    'unique_voters': 'Unique Voters',
    'crowdfunded_usd': 'Total Crowdfunded ($)',
    'last_donation': 'Last Donation',
    'matchingfunds': 'Total Matching Funds ($)'

})
filtered_columns = [col for col in round_df.columns if col not in ['Program Number', 'Last Donation']]

y_axis_column = st.selectbox('Select Y-Axis', filtered_columns)

# Create a bar graph with round_num on the x-axis and the selected column on the y-axis
fig = px.bar(round_df, x='Program Number', y=y_axis_column)
fig.update_traces(texttemplate='%{y:.2s}', textposition='outside')
st.plotly_chart(fig, use_container_width=True)


