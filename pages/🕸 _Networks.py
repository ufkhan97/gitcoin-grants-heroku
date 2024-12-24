import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import networkx as nx
import time
import utils

st.set_page_config(
    page_title="Data - Gitcoin Networks",
    page_icon="assets/favicon.png",
    layout="wide",
)

st.title('🕸 Network Analysis: Gitcoin Grants')
st.write('This interactive network visualization displays connections between donors and projects in the Gitcoin Grants Rounds. Explore relationships by zooming, panning, and hovering over nodes to view details.')
st.write('The visualization helps identify patterns such as projects with unique donor bases and community clustering.')

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


# After round selection
option = st.selectbox(
    'Select Round',
    dfr['options'].unique())

# Filter data for selected round
dfr = dfr[dfr['options'] == option]

# Get voters data for network graph
round_chain_pairs = [
    (str(row['round_id']).lower(), str(row['chain_id'])) 
    for _, row in dfr.iterrows()
]
votes_by_voter_and_project = utils.get_voters_by_project(round_chain_pairs)


# Minimum donation amount filter
min_donation = st.slider('Minimum donation amount', value=5, max_value=50, min_value=1, step=1)
votes_filtered = votes_by_voter_and_project[votes_by_voter_and_project['amountUSD'] > min_donation]

count_connections = votes_filtered.shape[0]
count_voters = votes_filtered['voter_id'].nunique()
count_grants = votes_filtered['project_name'].nunique()

# Check if the number of connections exceeds 10,000
if votes_filtered.shape[0] > 10000:
    # Calculate the fraction to sample
    frac_to_sample = 10000 / votes_filtered.shape[0]
    votes_filtered = votes_filtered.sample(frac=frac_to_sample, random_state=42)

count_connections = votes_filtered.shape[0]
count_voters = votes_filtered['voter_id'].nunique()
count_grants = votes_filtered['project_name'].nunique()


color_toggle = st.checkbox('Toggle colors', value=True)

if color_toggle:
    grants_color = '#00433B'
    grantee_color_string = 'moss'
    voters_color = '#C4F092'
    voter_color_string = 'lightgreen'
    line_color = '#6E9A82'
else:
    grants_color = '#FF7043'
    grantee_color_string = 'orange'
    voters_color = '#B3DE9F'
    voter_color_string = 'green'
    line_color = '#6E9A82'

note_string = f'**Network Summary:** {count_grants} Projects | {count_voters} Donors | {count_connections} Connections'
st.markdown(note_string)
st.markdown('*Use fullscreen mode (↗️) for optimal viewing*')
# Initialize a new Graph
B = nx.Graph()

# Create nodes with the bipartite attribute
B.add_nodes_from(votes_filtered['voter_id'].unique(), bipartite=0, color=voters_color) 
B.add_nodes_from(votes_filtered['project_name'].unique(), bipartite=1, color=grants_color) 



# Add edges with amountUSD as an attribute
for _, row in votes_filtered.iterrows():
    B.add_edge(row['voter_id'], row['project_name'], amountUSD=row['amountUSD'])



# Compute the layout
current_time = time.time()
pos = nx.spring_layout(B, dim=3, k = .09, iterations=50)
new_time = time.time()


    
# Extract node information
node_x = [coord[0] for coord in pos.values()]
node_y = [coord[1] for coord in pos.values()]
node_z = [coord[2] for coord in pos.values()] # added z-coordinates for 3D
node_names = list(pos.keys())
# Compute the degrees of the nodes 
degrees = np.array([B.degree(node_name) for node_name in node_names])
# Apply the natural logarithm to the degrees 
log_degrees = np.log(degrees + 1)
# Min-Max scaling manually
#min_size = 10  # minimum size
#max_size = 50  # maximum size
#node_sizes = ((log_degrees - np.min(log_degrees)) / (np.max(log_degrees) - np.min(log_degrees))) * (max_size - min_size) + min_size
node_sizes = log_degrees * 10

# Extract edge information
edge_x = []
edge_y = []
edge_z = []  
edge_weights = []

for edge in B.edges(data=True):
    x0, y0, z0 = pos[edge[0]]
    x1, y1, z1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])
    edge_z.extend([z0, z1, None])  
    edge_weights.append(edge[2]['amountUSD'])

# Create the edge traces
edge_trace = go.Scatter3d(
    x=edge_x, y=edge_y, z=edge_z, 
    line=dict(width=1, color=line_color),
    hoverinfo='none',
    mode='lines',
    marker=dict(opacity=0.5))


# Create the node traces
node_trace = go.Scatter3d(
    x=node_x, y=node_y, z=node_z,
    mode='markers',
    hoverinfo='text',
    marker=dict(
        color=[data['color'] for _, data in B.nodes(data=True)],  # color is now assigned based on node data
        size=node_sizes,
        opacity=1,
        sizemode='diameter'
    ))


node_adjacencies = []
for node, adjacencies in enumerate(B.adjacency()):
    node_adjacencies.append(len(adjacencies[1]))
node_trace.marker.color = [data[1]['color'] for data in B.nodes(data=True)]


# Prepare text information for hovering
node_trace.text = [f'{name}: {adj} connections' for name, adj in zip(node_names, node_adjacencies)]

# Create the figure
fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title='3D Network graph of voters and grants',
                    titlefont=dict(size=20),
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[ dict(
                        showarrow=False,
                        text="This graph shows the connections between voters and grants based on donation data.",
                        xref="paper",
                        yref="paper",
                        x=0.005,
                        y=-0.002 )],
                    scene = dict(
                        xaxis_title='X Axis',
                        yaxis_title='Y Axis',
                        zaxis_title='Z Axis')))
                        
st.plotly_chart(fig, use_container_width=True)
st.caption('Time to compute layout: ' + str(round(new_time - current_time, 2)) + ' seconds')
