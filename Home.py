import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import utils
from datetime import datetime
import numpy as np

st.set_page_config(
    page_title="Data - Gitcoin Grants",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

## DEPLOYED ON HEROKU 
# https://gitcoin-grants-51f2c0c12a8e.herokuapp.com/


def get_cumulative_amountUSD_time_series_chart(dfv, starting_time, ending_time, color_map):
    dfv_grouped = dfv.groupby(['round_name', dfv['block_timestamp'].dt.floor('H')])['amountUSD'].sum().reset_index()
    dfv_grouped.set_index(['round_name', 'block_timestamp'], inplace=True)
    dfv_grouped = dfv_grouped.reindex(pd.MultiIndex.from_product([dfv_grouped.index.get_level_values(0).unique(), pd.date_range(start=dfv_grouped.index.get_level_values(1).min(), end=dfv_grouped.index.get_level_values(1).max(), freq='H')], names=['round_name', 'block_timestamp']), fill_value=0)
    dfv_cumulative = dfv_grouped.groupby(level=0).cumsum()
    fig = px.area(dfv_cumulative, x=dfv_cumulative.index.get_level_values(1), y='amountUSD', color=dfv_cumulative.index.get_level_values(0), labels={'amountUSD': 'Total Donations (USD)', 'block_timestamp': 'Time'}, title='Cumulative Donations Over Time (USD) by Round', color_discrete_map=color_map)
    fig.update_layout(xaxis_range=[starting_time, min(ending_time, dfv['block_timestamp'].max())], showlegend=True, legend_title_text='Round')
    fig.update_xaxes(title_text='Time', nticks=5)
    fig.update_yaxes(tickprefix="$", tickformat="2s", title_text='Cumulative Donations (USD)')
    fig.update_traces(hovertemplate='<b>Round:</b> %{fullData.name}<br><b>Time:</b> %{x}<br><b>Total Donations:</b> $%{y:,.2f}')
    return fig

def create_token_distribution_chart(dfv):
    # Group by token and sum the amountUSD
    token_data = dfv.groupby('token_code')['amountUSD'].sum().reset_index()
    token_data = token_data.sort_values('amountUSD', ascending=False)
    
    # Calculate percentages
    total = token_data['amountUSD'].sum()
    token_data['percentage'] = token_data['amountUSD'] / total * 100

    # Create the donut chart
    fig = go.Figure(data=[go.Pie(
        labels=token_data['token_code'],
        values=token_data['amountUSD'],
        hole=.4,
        textinfo='label+percent',
        hovertemplate="<b>%{label}</b><br>Amount: $%{value:.2f}<br>Percentage: %{percent}<extra></extra>",
        marker=dict(colors=['#8e81f0', '#ff6b6b', '#feca57']),  # Adjust colors as needed
    )])

    fig.update_layout(
        title="Contributions (in USD) by Token",
        annotations=[dict(text='Total<br>$' + f"{total:.2f}", x=0.5, y=0.5, font_size=20, showarrow=False)],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

def calculate_qf_score(donations):
    return (np.sum(np.sqrt(donations)))**2

def create_project_highlights(dfv, dfp):

    # Prepare data (same as before)
    project_metrics = dfv.groupby('projectId').agg({
        'amountUSD': 'sum',
        'voter': 'nunique',
        'id': 'count'
    }).reset_index()

    project_metrics = project_metrics.merge(dfp[['projectId', 'title']], on='projectId', how='left').drop_duplicates(subset=['title'])

    # Calculate trending score based on quadratic funding in the last 24 hours
    last_24h = dfv['block_timestamp'].max() - pd.Timedelta(hours=24)
    recent_dfv = dfv[dfv['block_timestamp'] > last_24h]
    
    trending = recent_dfv.groupby('projectId').agg({
        'amountUSD': lambda x: calculate_qf_score(x),
        'voter': 'nunique'
    }).reset_index()
    trending.columns = ['projectId', 'qf_score', 'recent_donors']
    project_metrics = project_metrics.merge(trending, on='projectId', how='left')
    project_metrics['qf_score'] = project_metrics['qf_score'].fillna(0)
    
    # Normalize QF score
    max_qf_score = project_metrics['qf_score'].max()
    project_metrics['normalized_qf_score'] = project_metrics['qf_score'] / max_qf_score if max_qf_score > 0 else 0

    # Create visualization
    fig = go.Figure()

    # Scatter plot for all projects
    fig.add_trace(go.Scatter(
        x=project_metrics['voter'],
        y=project_metrics['amountUSD'],
        mode='markers',
        marker=dict(
            size=project_metrics['id'],
            sizemode='area',
            sizeref=2.*max(project_metrics['id'])/(40.**2),
            sizemin=4,
            color='#8e81f0',
            opacity=0.7
        ),
        text=project_metrics['title'],
        hovertemplate="<b>%{text}</b><br>" +
                      "Total Raised: $%{y:,.2f}<br>" +
                      "Unique Donors: %{x}<br>",
        showlegend=False  
    ))

    # Highlight top projects
    top_funded = project_metrics.nlargest(3, 'amountUSD')
    top_donors = project_metrics.nlargest(3, 'voter')
    top_trending = project_metrics.nlargest(3, 'normalized_qf_score')

    for df in [top_funded, top_donors, top_trending]:
        fig.add_trace(go.Scatter(
            x=df['voter'],
            y=df['amountUSD'],
            mode='markers+text',
            marker=dict(size=20, symbol='star', color='#FF6B6B', line=dict(width=2, color='DarkSlateGrey')),
            text=df['title'],
            textposition="top center",
            hoverinfo='skip',
            showlegend=False
        ))

    fig.update_layout(
        #title=None,
        xaxis_title="Unique Donors",
        yaxis_title="Total Raised (USD)",
        height=600,
        plot_bgcolor='white',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor='black',
            linewidth=2,
            showline=True,
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor='black',
            linewidth=2,
            showline=True,
        ),
        font=dict(family="monospace"),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Legend
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🏆 Top Funded")
        for _, project in top_funded.iterrows():
            st.write(f"**{project['title']}**: ${project['amountUSD']:,.2f}")
    with col2:
        st.subheader("👥 Most Donors")
        for _, project in top_donors.iterrows():
            st.write(f"**{project['title']}**: {project['voter']:,}")
    with col3:
        st.subheader("🚀 Trending (Last 24h)")
        for _, project in top_trending.iterrows():
            st.write(f"**{project['title']}**")

def get_combined_donation_chart(dfv, starting_time, ending_time, color_map):
    # Prepare data (same as before)
    dfv_count = dfv.groupby([dfv['block_timestamp'].dt.floor('H')])['id'].nunique().reset_index()
    dfv_count.set_index('block_timestamp', inplace=True)
    dfv_count = dfv_count.reindex(pd.date_range(start=dfv_count.index.min(), end=dfv_count.index.max(), freq='H'), fill_value=0)
    
    dfv_grouped = dfv.groupby([dfv['block_timestamp'].dt.floor('H')])['amountUSD'].sum().cumsum().reset_index()
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add traces
    fig.add_trace(
        go.Bar(x=dfv_count.index, y=dfv_count['id'], name="Hourly Contributions", marker_color='#8e81f0'),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=dfv_grouped['block_timestamp'], y=dfv_grouped['amountUSD'], 
                   name="Cumulative Donations", line=dict(color='#000000', width=2)),
        secondary_y=True,
    )
    
    # Update layout to match the theme
    fig.update_layout(
        title="Hourly Contributions and Cumulative Donations",
        font=dict(family="monospace", size=12),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date",
            gridcolor='#ffffff'
        ),
        yaxis=dict(gridcolor='#ffffff'),
        yaxis2=dict(gridcolor='#ffffff'),
        height = 550
    )
    
    # Set axis titles and range
    fig.update_xaxes(title_text="Time", range=[starting_time, min(ending_time, dfv['block_timestamp'].max())])
    fig.update_yaxes(title_text="Number of Contributions", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative Donations (USD)", secondary_y=True, tickprefix="$", tickformat=",.0f")
    
    return fig

@st.cache_data(ttl=3600)
def generate_round_summary(dfv, dfp, dfr):
    # Use dfr for round information
    round_summary = dfr[['round_name', 'amountUSD', 'uniqueContributors', 'match_amount_in_usd']]
    round_summary = round_summary.rename(columns={
        'amountUSD': 'total_donated',
        'uniqueContributors': 'unique_donors',
        'match_amount_in_usd': 'matching_pool'
    })
    
    # Get project count from dfp
    project_count = dfp.groupby('round_name')['projectId'].nunique().reset_index()
    project_count.columns = ['round_name', 'project_count']
    round_summary['matching_pool'] = round_summary['matching_pool'].round(-3)
    
    # Merge project count with round summary
    round_summary = pd.merge(round_summary, project_count, on='round_name')
    
    # Calculate the ratio of crowdfunding to matching funding
    round_summary['crowdfunding_to_matching_ratio'] = round_summary.apply(
        lambda row: f"{row['matching_pool']/(row['total_donated']  ) if row['total_donated'] != 0 else row['matching_pool']:.1f}x", axis=1)
    
    # Generate hourly contribution data
    def create_hourly_contributions(group):
        timestamps = pd.to_datetime(group['block_timestamp'])
        hourly_counts = timestamps.dt.floor('H').value_counts().sort_index()
        hourly_counts = hourly_counts.reindex(pd.date_range(start=hourly_counts.index.min(), 
                                                            end=hourly_counts.index.max(), 
                                                            freq='H'), 
                                              fill_value=0)
        return pd.Series({'hourly_contributions': hourly_counts.tolist()})

    time_series = dfv.groupby('round_name').apply(create_hourly_contributions).reset_index()
    round_summary = pd.merge(round_summary, time_series, on='round_name', how='left')
    
    # Sort by total donated in descending order
    round_summary = round_summary.sort_values('total_donated', ascending=False)
    
    return round_summary

@st.cache_resource(ttl=3600)
def create_treemap(dfv):
    votes_by_voter_and_project = dfv.groupby(['voter_id', 'project_name'])['amountUSD'].sum().reset_index()
    votes_by_voter_and_project['voter_id'] = votes_by_voter_and_project['voter_id'].str[:10] + '...'
    votes_by_voter_and_project['shortened_title'] = votes_by_voter_and_project['project_name'].str[:15] + '...'
    
    fig = px.treemap(votes_by_voter_and_project, path=['shortened_title', 'voter_id'], values='amountUSD', hover_data=['project_name', 'amountUSD'])
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

def create_project_spotlight(dfv, dfp):
    st.header("Project Spotlight")

    # Prepare data
    project_metrics = dfv.groupby(['projectId', pd.Grouper(key='block_timestamp', freq='H')]).agg({
        'amountUSD': 'sum',
        'voter': 'nunique',
        'id': 'count'
    }).reset_index()

    project_metrics = project_metrics.merge(dfp[['projectId', 'title']], on='projectId', how='left')
    
    # Get top 10 projects by total raised
    top_projects = project_metrics.groupby('projectId').agg({
        'amountUSD': 'sum',
        'voter': 'nunique',
        'id': 'count',
        'title': 'first'
    }).nlargest(10, 'amountUSD')

    # Create interactive project selector
    selected_project = st.selectbox("Select a project to spotlight", 
                                    options=top_projects.index, 
                                    format_func=lambda x: top_projects.loc[x, 'title'])

    project_data = project_metrics[project_metrics['projectId'] == selected_project]

    # Create subplot figure
    fig = make_subplots(rows=2, cols=2, 
                        subplot_titles=("Cumulative Donations", "Hourly Donations", 
                                        "Unique Donors", "Donations vs Donors"),
                        specs=[[{"secondary_y": True}, {"secondary_y": True}],
                               [{"secondary_y": True}, {"type": "scatter"}]])

    # Cumulative Donations
    cumulative = project_data['amountUSD'].cumsum()
    fig.add_trace(go.Scatter(x=project_data['block_timestamp'], y=cumulative, 
                             name="Cumulative Donations"), row=1, col=1)

    # Hourly Donations
    fig.add_trace(go.Bar(x=project_data['block_timestamp'], y=project_data['amountUSD'], 
                         name="Hourly Donations"), row=1, col=2)

    # Unique Donors
    cumulative_donors = project_data['voter'].cumsum()
    fig.add_trace(go.Scatter(x=project_data['block_timestamp'], y=cumulative_donors, 
                             name="Cumulative Donors"), row=2, col=1)

    # Donations vs Donors scatter
    fig.add_trace(go.Scatter(x=project_data['voter'], y=project_data['amountUSD'], 
                             mode='markers', name="Donations vs Donors"), row=2, col=2)

    # Update layout
    fig.update_layout(height=800, title_text=f"Spotlight: {top_projects.loc[selected_project, 'title']}")
    fig.update_xaxes(title_text="Time", row=1, col=1)
    fig.update_xaxes(title_text="Time", row=1, col=2)
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_xaxes(title_text="Unique Donors", row=2, col=2)
    fig.update_yaxes(title_text="USD", row=1, col=1)
    fig.update_yaxes(title_text="USD", row=1, col=2)
    fig.update_yaxes(title_text="Donors", row=2, col=1)
    fig.update_yaxes(title_text="Donation Amount (USD)", row=2, col=2)

    st.plotly_chart(fig, use_container_width=True)

    # Project Stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Raised", f"${top_projects.loc[selected_project, 'amountUSD']:,.2f}")
    col2.metric("Unique Donors", f"{top_projects.loc[selected_project, 'voter']:,}")
    col3.metric("Total Contributions", f"{top_projects.loc[selected_project, 'id']:,}")

    # Recent Activity
    st.subheader("Recent Activity")
    recent = project_data.nlargest(10, 'block_timestamp')[['block_timestamp', 'amountUSD', 'voter']]
    recent['block_timestamp'] = recent['block_timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    st.table(recent)


#col3.metric('Total Transactions', '{:,.0f}'.format(dfv['transaction_hash'].nunique()))


st.image('assets/657c7ed16b14af693c08b92d_GTC-Logotype-Dark.png', width = 200)
st.write('')
st.write('This page highlights some of the key metrics and insights from the recent Gitcoin Grants Programs. Select a program below to get started!')

program_data = pd.read_csv("data/all_rounds.csv")
program_option = st.selectbox( 'Select Program', program_data['program'].unique())
st.header(program_option + ' Summary')

if "program_option" in st.session_state and st.session_state.program_option != program_option:
    st.session_state.data_loaded = False
st.session_state.program_option = program_option


if "data_loaded" in st.session_state and st.session_state.data_loaded:
    dfv = st.session_state.dfv
    dfp = st.session_state.dfp
    dfr = st.session_state.dfr
    round_data = st.session_state.round_data
else:
    data_load_state = st.text('Loading data...')
    dfv, dfp, dfr, round_data = utils.load_round_data(program_option, "data/all_rounds.csv")
    data_load_state.text("")

if program_option == 'GG21':
    time_left = utils.get_time_left(pd.to_datetime('2024-08-21 23:59:59', utc=True))
    st.write('')
    if time_left != '0 days   0 hours   0 minutes':
        st.write('⏰ Time Left: ' + time_left)
    else:
        st.subheader('🎉 Round Complete 🎉')

col1, col2, col3 = st.columns(3)
col1.metric('Matching Pool', '${:,.0f}'.format(dfr['match_amount_in_usd'].apply(lambda x: round(x, -3)).sum())) 
col1.metric('Total Donated', '${:,.0f}'.format(dfv['amountUSD'].sum()))
col2.metric("Total Donations", '{:,.0f}'.format(dfp['votes'].sum()))
col2.metric('Unique Donors', '{:,.0f}'.format(dfv['voter'].nunique()))
col3.metric('Total Rounds', '{:,.0f}'.format(dfr.shape[0]))
col3.metric('Total Projects', '{:,.0f}'.format(len(dfp)))
    
starting_time = pd.to_datetime(dfr['donations_start_time'].min(), utc=True)
ending_time = pd.to_datetime(dfr['donations_end_time'].max(), utc=True)
color_map = dict(zip(dfp['round_name'].unique(), px.colors.qualitative.Pastel))

col1, col2 = st.columns([2, 1])
with col1:
    st.plotly_chart(get_combined_donation_chart(dfv, starting_time, ending_time, color_map), use_container_width=True)
with col2:
    st.plotly_chart(create_token_distribution_chart(dfv), use_container_width=True)

st.header("Project Highlights")
create_project_highlights(dfv, dfp)


# Display round summary table with column configs
round_summary = generate_round_summary(dfv, dfp, dfr)
st.header("Rounds Summary")
st.dataframe(
    round_summary,
    column_config={
        "round_name": st.column_config.TextColumn("Round Name"),
        "project_count": st.column_config.NumberColumn("Project Count", format="%d"),
        "matching_pool": st.column_config.NumberColumn("Matching Pool (USD)", format="$%.0f"),
        "unique_donors": st.column_config.NumberColumn("Unique Donors", format="%d"),
        "total_donated": st.column_config.NumberColumn("Total Donated", format="$%.2f"),
        "crowdfunding_to_matching_ratio": st.column_config.TextColumn("Avg. Matching Multiple"),
        "hourly_contributions": st.column_config.LineChartColumn("Hourly Contributions")
    },
    hide_index=True,
    height=38 + (len(round_summary) * 35)   # header_height + (num_rows * row_height) + padding

)


if dfp['round_id'].nunique() > 1:

    st.title("Round Details")
    # selectbox to select the round
    option = st.selectbox(
        'Select Round',
        dfr['options'].unique())
    option = option.split(' - ')[0]
    dfv = dfv[dfv['round_name'] == option]
    dfp = dfp[dfp['round_name'] == option]
    dfr = dfr[dfr['round_name'] == option]
    dfp['votes'] = dfp['votes'].astype(int)
    dfp['amountUSD'] = dfp['amountUSD'].astype(float)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('Matching Pool', '${:,.0f}'.format(dfr['match_amount_in_usd'].sum()))
    col2.metric('Total Donated', '${:,.0f}'.format(dfp['amountUSD'].sum()))
    col3.metric('Total Donations',  '{:,.0f}'.format(dfp['votes'].sum()))
    col4.metric('Total Projects',  '{:,.0f}'.format(len(dfp)))
    col5.metric('Unique Donors',  '{:,.0f}'.format(dfv['voter'].nunique()))

treemap_dfv = dfv[dfv['projectId'].isin(dfp['projectId'])].copy()
st.plotly_chart(create_treemap(treemap_dfv), use_container_width=True)

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


#create_project_spotlight(dfv, dfp)
