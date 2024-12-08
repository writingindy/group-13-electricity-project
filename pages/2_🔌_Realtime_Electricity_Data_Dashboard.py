import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm
import warnings
import plotly.express as px
import gridstatus
import datetime
import time
import psycopg2

warnings.filterwarnings('ignore')

st.set_page_config(
    layout="wide",
    page_title='Real-Time Electricity Data Dashboard',
    page_icon=':electric_plug',
)

### Global Variables and Helper Functions

data_map = {'nyiso_load': 'New York', 
                'nyiso_fuel_mix': 'New York',
                'caiso_load': 'California',
                'caiso_fuel_mix': 'California',
                'isone_load': 'New England',
                'isone_fuel_mix': 'New England'}

nyiso_fuel_sources = [
    'dual_fuel', 'hydro', 'natural_gas', 'nuclear',
    'other_fossil_fuels', 'other_renewables', 'wind']

caiso_fuel_sources = [
    'solar', 'wind', 'geothermal', 'biomass', 'biogas', 'small_hydro', 'coal', 'nuclear', 'natural_gas', 'large_hydro', 'batteries', 'imports', 'other']

isone_fuel_sources = [
    'coal', 'hydro', 'landfill_gas', 'natural_gas', 'nuclear', 'oil', 'refuse', 'solar', 'wind', 'wood', 'other']

@st.cache_data
def get_day_data(table):
    today = datetime.date.today()
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    #today = pd.to_datetime('2024-11-26')
    #tomorrow = pd.to_datetime('2024-11-27')

    conn = st.connection("postgresql", type="sql")
    
    res = conn.query(f"SELECT * FROM {table} WHERE time >= \'{today}\' AND time < \'{tomorrow}\';", ttl="10m")
    res = res.sort_values(by='time')

    return res


def plot_day_load(table):
    data = get_day_data(table)
    data_copy = data.copy()

    
    start_time = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0))
    end_time = datetime.datetime.combine(datetime.date.today(), datetime.time(23, 59))
    
    fig = plt.figure(figsize=(12, 6))
    ax = fig.gca()
    ax.set_xlim(start_time, end_time)



    #data_copy['time'] = pd.to_datetime(data_copy['time'])
    #data_copy.set_index('time', inplace=True)

    #data_copy['Hour'] = data_copy.index.hour
    
    plt.plot(data_copy['time'], data_copy['load'], color='blue', linewidth=3, label='Real Load')
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

    return fig

## Streamlit Web App: Dashboard portion

st.title(":electric_plug: Real-Time Electricity Data Dashboard")

st.header('Live Dashboard', divider='gray')


nyiso_tab, caiso_tab, isone_tab = st.tabs(["NYISO", "CAISO", "ISONE"])
nyiso_tab.pyplot(plot_day_load('nyiso_load'))
caiso_tab.pyplot(plot_day_load('caiso_load'))
isone_tab.pyplot(plot_day_load('isone_load'))
