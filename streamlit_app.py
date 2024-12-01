import streamlit as st
import pandas as pd
import warnings
import gridstatus
import psycopg2
from st_pages import add_page_title, get_nav_from_toml

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title='Electricity Data Dashboard',
    page_icon=':electric_plug:', # This is an emoji shortcode. Could be a URL too.
)

st.set_page_config(layout="wide")

# If you want to use the no-sections version, this
# defaults to looking in .streamlit/pages.toml, so you can
# just call `get_nav_from_toml()`
nav = get_nav_from_toml(".streamlit/pages_sections.toml")


pg = st.navigation(nav)

add_page_title(pg)

pg.run()


st.title("Electricity Data Dashboard")


'''
This web app will present some exploratory data analysis on electricity data, gathered from the gridstatus API.
'''

@st.cache_data
def load_table_based_on_timerange(timemin, timemax, table):
    
    conn = st.connection("postgresql", type="sql")
    if timemax is None:
        res = conn.query(f"SELECT * FROM {table} WHERE time >= \'{timemin}\';", ttl="10m")
    else:
        res = conn.query(f"SELECT * FROM {table} WHERE time >= \'{timemin}\' AND time < \'{timemax}\';", ttl="10m")
    
    return res


