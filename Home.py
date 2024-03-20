import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import utils 

st.set_page_config(
    page_title="Data - Gitcoin Stats",
    page_icon="favicon.png",
    layout="wide",
)

#st.title('📈 Stats')

st.image('657c7ed16b14af693c08b92d_GTC-Logotype-Dark.png', width = 300)
st.write('')
st.write('The Gitcoin Grants Program is a quarterly initiative that empowers individuals to drive funding toward what they believe matters, with the impact of their contribution being magnified by the use of the [Quadratic Funding (QF)](https://wtfisqf.com) distribution mechanism.')
st.write('👉 Visit [grants.gitcoin.co](https://grants.gitcoin.co) to donate to your favorite projects.')
st.write('👉 If you find this tool valuable, make a donation to the Gitcoin Matching Pool: gitcoin.eth (mainnet)')



cf = utils.run_query_from_file('queries/get_summary_stats.sql')


last_updated = cf['last_donation'][0].strftime('%Y-%m-%d')
st.write('Last run: ' + last_updated)
col1, col2, col3 = st.columns(3)
col1.metric(label="Total Unique Grants", value='{:,.0f}'.format(cf['unique_grantees'][0]))
col2.metric(label="Total Donations", value='{:,.0f}'.format(cf['num_donations'][0]) )
col3.metric(label="Total Unique Voters", value='{:,.0f}'.format(cf['unique_voters'][0]))

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


