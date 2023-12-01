import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import utils 

st.set_page_config(
    page_title="Data - Gitcoin Leaderboard",
    page_icon="favicon.png",
    layout="wide",
)

st.title('💸 Projects and their donors')

st.write("This page gives you the list of donors for a particular project after you enter the project id.The projectid should have the same capitalization as is given in gitcoin")

st.write("test - test")

project_id = st.text_input('Enter Project ID', 'none')



program_data = pd.read_csv("all_rounds.csv")
program_option = st.selectbox( 'Select Program', program_data['program'].unique())
st.title(program_option)

