import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import warnings
import plotly.express as px
import gridstatus
import datetime
import time
import psycopg2

warnings.filterwarnings('ignore')

st.set_page_config(
    #layout="wide",
    page_title='Big Data Management Systems: Group 13 Project',
    page_icon='👋',
)

### Web App by Streamlit

st.title("👋 Big Data Management Systems: Group 13 Project")

'''
This web app has two sections:
- The first section will present a live dashboard of the current day's electricity load and fuel mix, as well as the forecasted load.
- The second section will present some interactive exploratory data analysis on electricity load and fuel mix data, gathered from the gridstatus API.
'''

