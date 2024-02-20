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

st.title('📈 Stats')

stats = utils.run_query_from_file('queries/get_cumulative_stats.sql')
st.write(stats)
