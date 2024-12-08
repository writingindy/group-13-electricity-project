import streamlit as st
import numpy as np
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

if not "sleep_time" in st.session_state:
    #st.session_state.sleep_time = 15
    st.session_state.sleep_time = 5*60

if not "auto_refresh" in st.session_state:
    st.session_state.auto_refresh = True

auto_refresh = st.sidebar.checkbox('Auto Refresh?', st.session_state.auto_refresh)

if auto_refresh:
    #st.session_state.sleep_time = 15
    st.session_state.sleep_time = 5*60


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


def get_day_data(table):
    today = datetime.date.today()
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    #today = pd.to_datetime('2024-11-26')
    #tomorrow = pd.to_datetime('2024-11-27')

    conn = st.connection("postgresql", type="sql")
    
    res = conn.query(f"SELECT * FROM {table} WHERE time >= \'{today}\' AND time < \'{tomorrow}\';", ttl="10m")
    res = res.sort_values(by='time')


    return res


def plot_day_data(table):
    data = get_day_data(table)
    data_copy = data.copy()

    start_time = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0))
    end_time = datetime.datetime.combine(datetime.date.today(), datetime.time(23, 59))
    
    fig = plt.figure(figsize=(18, 12))
    
    if 'load' in table:
        ax = fig.gca()
        ax.set_xlim(start_time, end_time)
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        plt.grid()
        plt.xlabel('Hour of Day', fontsize=12)
        plt.ylabel('Load (MW)', fontsize=12)
        plt.title(f'Realtime {data_map[table]} Load Data', fontsize=16)
        

        plt.plot(data_copy['time'], data_copy['load'], color='blue', linewidth=3, label='Real Load')
        plt.legend(title="Load", bbox_to_anchor=(1.05, 1), loc='upper right')
    elif 'fuel_mix' in table:
        ax = fig.gca()
        ax.set_xlim(start_time, end_time)
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        plt.grid()
        plt.xlabel('Hour of Day', fontsize=12)
        plt.ylabel('Total Energy Generation (MW)', fontsize=12)
        plt.title(f'Realtime {data_map[table]} Fuel Mix', fontsize=16)
        if 'nyiso' in table or 'isone' in table:
            y = data_copy.drop(columns=['time', 'index']).clip(lower=0)
            y = y.fillna(0)
            plt.stackplot(data_copy['time'], y.T, labels=y.columns)
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')
        elif 'caiso' in table:
            y = data_copy.drop(columns=['time', 'index', 'interval_start', 'interval_end']).clip(lower=0)
            y = y.fillna(0)
            plt.stackplot(data_copy['time'], y.T, labels=y.columns)
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')
    return fig


## Streamlit Web App: Dashboard portion

st.title(":electric_plug: Real-Time Electricity Data Dashboard")

st.header('Live Dashboard', divider='gray')

nyiso_placeholder = st.empty()
nyiso_tab, caiso_tab, isone_tab = st.tabs(["NYISO", "CAISO", "ISONE"])

#for five_min_interval in range(288):
with nyiso_tab.container():
    nyiso_load = nyiso_tab.plotly_chart(plot_day_data('nyiso_load'), theme=None, use_container_width=True)
    nyiso_load.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)', 'paper_bgcolor': 'rgba(0, 0, 0, 0)',})
    nyiso_tab.pyplot(plot_day_data('nyiso_fuel_mix'))

with caiso_tab.container():
    caiso_tab.pyplot(plot_day_data('caiso_load'))
    caiso_tab.pyplot(plot_day_data('caiso_fuel_mix'))

with isone_tab.container():
    isone_tab.pyplot(plot_day_data('isone_load'))
    isone_tab.pyplot(plot_day_data('isone_fuel_mix'))


if auto_refresh:
    #time.sleep(15)
    time.sleep(5*60)
    st.rerun()