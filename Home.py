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
    initial_sidebar_state="expanded"
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

def create_token_distribution_chart(hourly_contributions):
    # Group by token and sum the total_amount
    token_data = hourly_contributions.groupby('token_code')['total_amount'].sum().reset_index()
    token_data = token_data.sort_values('total_amount', ascending=False)
    
    # Calculate percentages
    total = token_data['total_amount'].sum()
    token_data['percentage'] = token_data['total_amount'] / total * 100

    # Define color mapping for common tokens
    token_colors = {
        'ETH': '#627eea',
        'OP': '#ff0420',
        'USDC': '#2775ca',
        'CELO': '#35d07f',
        'USDGLO': '#ffcc00',
        'ARB': '#28a0f0',
        'GTC': '#ff6b6b',
        'DAI': '#f4b731',
        'MATIC': '#8247e5'
    }
    
    # Assign colors to tokens, use a default color if not in the mapping
    token_data['color'] = token_data['token_code'].map(token_colors).fillna('#cccccc')

    # Create the donut chart
    fig = go.Figure(data=[go.Pie(
        labels=token_data['token_code'],
        values=token_data['total_amount'],
        hole=.4,
        textinfo='label+percent',
        hovertemplate="<b>%{label}</b><br>Amount: $%{value:.2f}<br>Percentage: %{percent}<extra></extra>",
        marker=dict(colors=token_data['color']),  # Use the mapped colors
    )])

    # Format total amount with appropriate suffix (K, M, B)
    if total >= 1e9:
        total_formatted = f"${total/1e9:.1f}B"
    elif total >= 1e6:
        total_formatted = f"${total/1e6:.1f}M"
    elif total >= 1e3:
        total_formatted = f"${total/1e3:.1f}K"
    else:
        total_formatted = f"${total:.2f}"

    fig.update_layout(
        title="Contributions (in USD) by Token",
        annotations=[dict(text=f'Total<br>{total_formatted}', x=0.5, y=0.5, font_size=16, showarrow=False)],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

def calculate_qf_score(donations):
    return (np.sum(np.sqrt(donations)))**2

def create_project_highlights(dfp):
    dfp['average_donation'] = dfp['amountUSD'] / dfp['votes']

    # Create visualization
    fig = go.Figure()

    # Scatter plot for all projects with log scale
    fig.add_trace(go.Scatter(
        x=dfp['votes'],
        y=dfp['amountUSD'],
        mode='markers',
        marker=dict(
            size=dfp['votes'],
            sizemode='area',
            sizeref=2.*max(dfp['votes'])/(25.**2),
            sizemin=4,
            color='#8e81f0',
            opacity=0.7
        ),
        text=dfp['title'],
        hovertemplate="<b>%{text}</b><br>" +
                      "Total Raised: $%{y:,.2f}<br>" +
                      "Unique Donors: %{x}<br>" +
                      "<extra></extra>",
        showlegend=False  
    ))

    # Highlight top projects
    top_funded = dfp.nlargest(3, 'amountUSD')
    top_donors = dfp.nlargest(3, 'votes')
    top_trending = dfp.nlargest(3, 'average_donation')


    fig.update_layout(
        #title=None,
        xaxis_title="Log. Unique Donors",
        yaxis_title="Log. Total Raised (USD)",
        height=600,
        plot_bgcolor='white',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor='black',
            linewidth=2,
            showline=True,
            type='log'
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor='black',
            linewidth=2,
            showline=True,
            type='log'
        ),
        font=dict(family="monospace"),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Legend
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🏆 Top Funded")
        for _, project in top_funded.iterrows():
            st.write(f"**{project['title'].strip()}**: ${project['amountUSD']:,.2f}")
    with col2:
        st.subheader("👥 Most Donors")
        for _, project in top_donors.iterrows():
            st.write(f"**{project['title'].strip()}**: {project['votes']:,}")
    with col3:
        st.subheader("💪🏾 Highest Average")
        for _, project in top_trending.iterrows():
            st.write(f"**{project['title'].strip()}**: ${project['average_donation']:,.2f}")

def get_combined_donation_chart(hourly_contributions, starting_time, ending_time, color_map):
    # Aggregate all tokens and chains by hour
    hourly_totals = hourly_contributions.groupby('hour')['total_amount'].sum().reset_index()
    
    # Calculate cumulative sum
    cumulative_totals = hourly_totals.copy()
    cumulative_totals['total_amount'] = cumulative_totals['total_amount'].cumsum()

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add hourly bars
    fig.add_trace(
        go.Bar(
            x=hourly_totals['hour'], 
            y=hourly_totals['total_amount'], 
            name="Hourly Contributions", 
            marker_color='#8e81f0'
        ),
        secondary_y=False,
    )
    
    # Add cumulative line
    fig.add_trace(
        go.Scatter(
            x=cumulative_totals['hour'], 
            y=cumulative_totals['total_amount'],
            name="Cumulative Donations", 
            line=dict(color='#000000', width=2)
        ),
        secondary_y=True,
    )
    
    # Update layout
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
        height=550
    )
    
    # Set axis titles and range
    fig.update_xaxes(title_text="Time", range=[starting_time, min(ending_time, hourly_totals['hour'].max())])
    fig.update_yaxes(title_text="Hourly Donations (USD)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative Donations (USD)", secondary_y=True, tickprefix="$", tickformat=",.0f")
    
    return fig

@st.cache_data(ttl=3600)
def generate_round_summary(hourly_contributions, dfp, dfr):
    # Initialize round summary with basic metrics
    round_summary = dfr[['round_name', 'amountUSD', 'uniqueContributors', 'match_amount_in_usd', 'chain_id', 'round_id']]
    round_summary = round_summary.rename(columns={
        'amountUSD': 'total_donated',
        'uniqueContributors': 'unique_donors',
        'match_amount_in_usd': 'matching_pool'
    })
    
    # Get project count per round
    project_count = dfp.groupby('round_name')['projectId'].nunique().reset_index()
    project_count.columns = ['round_name', 'project_count']
    
    # Round matching pool to nearest thousand
    round_summary['matching_pool'] = round_summary['matching_pool'].round(-3)
    
    # Merge project count with round summary
    round_summary = pd.merge(round_summary, project_count, on='round_name')
    
    # Calculate matching ratio
    round_summary['crowdfunding_to_matching_ratio'] = round_summary.apply(
        lambda row: f"{row['matching_pool']/(row['total_donated'] if row['total_donated'] != 0 else row['matching_pool']):.1f}x",
        axis=1
    )

    # Process hourly contributions
    hourly_data = hourly_contributions.groupby(['chain_id', 'round_id', 'hour'])['total_amount'].sum().reset_index()
    
    # Create time series for each round
    hourly_series = {}
    for chain_id, round_id in zip(hourly_data['chain_id'], hourly_data['round_id']):
        mask = (hourly_data['chain_id'] == chain_id) & (hourly_data['round_id'] == round_id)
        hourly_series[(chain_id, round_id)] = hourly_data[mask]['total_amount'].tolist()
    
    # Add hourly series to round summary
    round_summary['hourly_contributions'] = round_summary.apply(
        lambda row: hourly_series.get((row['chain_id'], row['round_id']), []),
        axis=1
    )
    
    # Create round URLs
    round_summary['round_url'] = round_summary.apply(
        lambda row: f"https://explorer.gitcoin.co/#/round/{row['chain_id']}/{row['round_id']}", 
        axis=1
    )
    
    # Sort by total donated
    round_summary = round_summary.sort_values('total_donated', ascending=False)
    # Select and order final columns
    round_summary = round_summary[[
        'round_name',
        'crowdfunding_to_matching_ratio',
        'round_url',
        'hourly_contributions',
        'project_count',
        'matching_pool',
        'unique_donors',
        'total_donated',
    ]]
    
    return round_summary

@st.cache_resource(ttl=3600)
def create_treemap(votes_by_voter_and_project):
    votes_by_voter_and_project['voter_id'] = votes_by_voter_and_project['voter_id'].str[:10] + '...'
    votes_by_voter_and_project['shortened_title'] = votes_by_voter_and_project['project_name'].apply(lambda x: x if len(x) <= 15 else x[:15] + '...')
    
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

dfr = utils.get_round_data()
program_option = st.selectbox( 'Select Program', dfr['program'].unique())
st.header(program_option + ' Summary')

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
        # WE HERE RIGHT NOW
    data_load_state.text("")

if program_option == 'GG22':
    time_left = utils.get_time_left(pd.to_datetime('2024-11-06 23:59:00', utc=True))
    st.write('')
    if time_left != '0 days   0 hours   0 minutes':
        st.write('⏰ Time Left: ' + time_left)
    #else:
        #st.subheader('🎉 Round Complete 🎉')

col1, col2, col3 = st.columns(3)
col1.metric('Matching Pool', '${:,.0f}'.format(dfr['match_amount_in_usd'].apply(lambda x: round(x, -3)).sum())) 
col1.metric('Total Donated', '${:,.0f}'.format(dfr['amountUSD'].sum()))
col2.metric("Total Donations", '{:,.0f}'.format(dfr['votes'].sum()))
col2.metric('Unique Donors', '{:,.0f}'.format(unique_donors['count'].iloc[0]))
col3.metric('Total Rounds', '{:,.0f}'.format(dfr.shape[0]))
col3.metric('Total Projects', '{:,.0f}'.format(len(dfp)))
    
starting_time = pd.to_datetime(dfr['donations_start_time'].min(), utc=True)
ending_time = pd.to_datetime(dfr['donations_end_time'].max(), utc=True)
color_map = dict(zip(dfp['round_name'].unique(), px.colors.qualitative.Pastel))

if dfr['amountUSD'].sum() < 1000:
    st.warning("🚀 You're early! We don't have data for this program yet. Try selecting a different program or check back soon for exciting updates!")
else:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(get_combined_donation_chart(hourly_contributions, starting_time, ending_time, color_map), use_container_width=True)
    with col2:
        st.plotly_chart(create_token_distribution_chart(hourly_contributions), use_container_width=True)

    st.header("Project Highlights")
    create_project_highlights(dfp)


    # Display round summary table with column configs
    round_summary = generate_round_summary(hourly_contributions, dfp, dfr)
    st.header("Rounds Summary")
    st.dataframe(
        round_summary,
        column_config={
            "round_name": st.column_config.TextColumn("Round Name"),
            "crowdfunding_to_matching_ratio": st.column_config.TextColumn("Match Multiple (Avg.)", width="small"),
            "round_url": st.column_config.LinkColumn("Round URL", display_text="Visit"),
            "hourly_contributions": st.column_config.LineChartColumn("Hourly Contributions"),
            "project_count": st.column_config.NumberColumn("Project Count", format="%d"),
            "matching_pool": st.column_config.NumberColumn("Matching Pool (USD)", format="$%.0f"),
            "unique_donors": st.column_config.NumberColumn("Unique Donors", format="%d"),
            "total_donated": st.column_config.NumberColumn("Total Donated", format="$%.2f")
        },
        hide_index=True,
        height=38 + (len(round_summary) * 35)   # header_height + (num_rows * row_height) + padding
    )

    st.header("Round Details")
    if dfp['round_id'].nunique() > 1:
        # selectbox to select the round
        option = st.selectbox(
            'Select Round',
            dfr['options'].unique())
        option = option.split(' | ')[0]
        dfp = dfp[dfp['round_name'] == option]
        dfr = dfr[dfr['round_name'] == option]
    dfp['Project Link'] = 'https://explorer.gitcoin.co/#/round/' + dfp['chain_id'].astype(str) + '/' + dfp['round_id'].astype(str) + '/' + dfp['projectId'].astype(str)
    df_display = dfp[['title', 'unique_donors_count', 'amountUSD', 'Project Link']].sort_values('unique_donors_count', ascending=False)
    
    st.dataframe(
        df_display,
        column_config={
            "title": st.column_config.TextColumn("Title"),
            "unique_donors_count": st.column_config.NumberColumn("Donors", format="%d"),
            "amountUSD": st.column_config.NumberColumn("Amount (USD)", format="$%.2f"),
            "Project Link": st.column_config.LinkColumn("Project", display_text="View")
        },
        hide_index=True,
        use_container_width=True,
        height=800
    )


    #create_project_spotlight(dfv, dfp)
