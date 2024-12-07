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
from st_pages import add_page_title, get_nav_from_toml


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




warnings.filterwarnings('ignore')

st.set_page_config(
    layout="wide",
    page_title='Electricity Data Dashboard',
    page_icon=':electric_plug:', # This is an emoji shortcode. Could be a URL too.
)


# If you want to use the no-sections version, this
# defaults to looking in .streamlit/pages.toml, so you can
# just call `get_nav_from_toml()`
#nav = get_nav_from_toml(".streamlit/pages_sections.toml")


#pg = st.navigation(nav)

#add_page_title(pg)



st.title(":electric_plug: Electricity Data Dashboard")


'''
This web app has two sections:
- The first section will present a live dashboard of the current day's electricity load and fuel mix, as well as the forecasted load.
- The second section will present some interactive exploratory data analysis on electricity load and fuel mix data, gathered from the gridstatus API.
'''

st.header('Live Dashboard', divider='gray')

#@st.cache_data
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
    
    fig = plt.figure(figsize=(12, 6))

    data_copy = data.copy()

    #data_copy['time'] = pd.to_datetime(data_copy['time'])
    #data_copy.set_index('time', inplace=True)

    #data_copy['Hour'] = data_copy.index.hour
    
    plt.plot(data_copy['time'], data_copy['load'], color='blue', linewidth=3, label='Average Load')

    return fig
    
    

#today_nyiso_load = get_day_data('nyiso_load')


nyiso_tab, caiso_tab, isone_tab = st.tabs(["NYISO", "CAISO", "ISONE"])
nyiso_tab.pyplot(plot_day_load('nyiso_load'))
caiso_tab.pyplot(plot_day_load('caiso_load'))
isone_tab.pyplot(plot_day_load('isone_load'))



@st.cache_data
def load_table_based_on_timerange(timemin, timemax, table):
    
    conn = st.connection("postgresql", type="sql")
    if timemax is None:
        res = conn.query(f"SELECT * FROM {table} WHERE time >= \'{timemin}\';", ttl="10m")
    else:
        res = conn.query(f"SELECT * FROM {table} WHERE time >= \'{timemin}\' AND time < \'{timemax}\';", ttl="10m")
    res = res.sort_values(by='time')
    return res

@st.cache_resource
def plot_monthly_table_based_on_timerange(timemin, timemax, table):
    data = load_table_based_on_timerange(timemin, timemax, table)



    if 'load' in table:
        data_type = 'load'
    else:
        data_type = 'fuel_mix'

    data_copy = data.copy()

    data_copy['time'] = pd.to_datetime(data_copy['time'])
    data_copy.set_index('time', inplace=True)

    data_copy['Year'] = data_copy.index.year
    data_copy['Month'] = data_copy.index.month

    monthly_avg_per_year = data_copy.groupby(['Year', 'Month']).mean().unstack(level=0)
    monthly_avg_overall = data_copy.groupby('Month').mean()

    bottoms = [0] * len(monthly_avg_overall)

    fig = plt.figure(figsize=(12, 7))

    
    if data_type == 'load':
        for year in data_copy['Year'].unique():
            monthly = monthly_avg_per_year[data_type][year]
            plt.plot(monthly.index, monthly, alpha=0.3, label=str(year))

        plt.plot(monthly_avg_overall.index, monthly_avg_overall[data_type], color='blue', linewidth=3, label='Average Load')
        plt.title(f'Historical {data_map[table]} Load Data - Monthly Averages', fontsize=16)
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Load (MW)', fontsize=12)

        plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
        plt.xlim([1, 12])

        plt.legend(title='Year', loc='upper right', bbox_to_anchor=(1.05, 1))
        plt.grid(True)
        plt.tight_layout()
    elif data_type == 'fuel_mix':
        if 'nyiso' in table:
            for fuel_source in nyiso_fuel_sources:
                plt.bar(monthly_avg_overall.index,
                    monthly_avg_overall[fuel_source],
                    bottom=bottoms,
                    label=fuel_source,
                    color=cm.get_cmap('tab20c', len(nyiso_fuel_sources))(nyiso_fuel_sources.index(fuel_source)),
                    alpha=0.7)
                bottoms = [bottom + value for bottom, value in zip(bottoms, monthly_avg_overall[fuel_source])]

            plt.title(f'Historical {data_map[table]} Fuel Mix - Monthly Averages', fontsize=16)
            plt.xlabel('Month', fontsize=12)
            plt.ylabel('Total Energy Generation (MW)', fontsize=12)


            plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            plt.xlim([1, 12])
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')


            plt.grid(True)
            plt.tight_layout()
        elif 'caiso' in table:
            for fuel_source in caiso_fuel_sources:
                plt.bar(monthly_avg_overall.index,
                    monthly_avg_overall[fuel_source],
                    bottom=bottoms,
                    label=fuel_source,
                    color=cm.get_cmap('tab20c', len(caiso_fuel_sources))(caiso_fuel_sources.index(fuel_source)),
                    alpha=0.7)
                bottoms = [bottom + value for bottom, value in zip(bottoms, monthly_avg_overall[fuel_source])]

            plt.title(f'Historical {data_map[table]} Fuel Mix - Monthly Averages', fontsize=16)
            plt.xlabel('Month', fontsize=12)
            plt.ylabel('Total Energy Generation (MW)', fontsize=12)


            plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            plt.xlim([1, 12])
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')


            plt.grid(True)
            plt.tight_layout()
        elif 'isone' in table:
            for fuel_source in isone_fuel_sources:
                plt.bar(monthly_avg_overall.index,
                    monthly_avg_overall[fuel_source],
                    bottom=bottoms,
                    label=fuel_source,
                    color=cm.get_cmap('tab20c', len(isone_fuel_sources))(isone_fuel_sources.index(fuel_source)),
                    alpha=0.7)
                bottoms = [bottom + value for bottom, value in zip(bottoms, monthly_avg_overall[fuel_source])]

            plt.title(f'Historical {data_map[table]} Fuel Mix - Monthly Averages', fontsize=16)
            plt.xlabel('Month', fontsize=12)
            plt.ylabel('Total Energy Generation (MW)', fontsize=12)


            plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            plt.xlim([1, 12])
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')


            plt.grid(True)
            plt.tight_layout()
    return fig

@st.cache_resource
def plot_weekly_table_based_on_timerange(timemin, timemax, table):
    data = load_table_based_on_timerange(timemin, timemax, table)

    if 'load' in table:
        data_type = 'load'
    else:
        data_type = 'fuel_mix'

    data_copy = data.copy()

    data_copy['time'] = pd.to_datetime(data_copy['time'])
    data_copy.set_index('time', inplace=True)

    data_copy['Year'] = data_copy.index.year
    data_copy['Weekday'] = data_copy.index.weekday

    weekday_avg_per_year = data_copy.groupby(['Year', 'Weekday']).mean().unstack(level=0)
    weekday_avg_overall = data_copy.groupby('Weekday').mean()

    bottoms = [0] * len(weekday_avg_overall)
    
    fig = plt.figure(figsize=(12, 7))

    if data_type == "load":
        for year in data_copy['Year'].unique():
            weekday_data = weekday_avg_per_year[data_type][year]
            plt.plot(weekday_data.index, weekday_data, alpha=0.3, label=str(year))

        plt.plot(weekday_avg_overall.index, weekday_avg_overall[data_type], color='blue', linewidth=3, label='Average Load')
        plt.title(f'Historical {data_map[table]} Load Data - Daily Averages by Weekday', fontsize=16)
        plt.xlabel('Weekday', fontsize=12)
        plt.ylabel('Load (MW)', fontsize=12)
        
        plt.xticks(range(0, 7), ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
        plt.xlim([0, 6])

        plt.legend(title='Year', loc='upper right', bbox_to_anchor=(1.05, 1))
        plt.grid(True)
        plt.tight_layout()
    elif data_type == "fuel_mix":
        if 'nyiso' in table:
            for fuel_source in nyiso_fuel_sources:
                plt.bar(weekday_avg_overall.index,
                    weekday_avg_overall[fuel_source],
                    bottom=bottoms,
                    label=fuel_source,
                    color=cm.get_cmap('tab20c', len(nyiso_fuel_sources))(nyiso_fuel_sources.index(fuel_source)),
                    alpha=0.7)
                bottoms = [bottom + value for bottom, value in zip(bottoms, weekday_avg_overall[fuel_source])]

            plt.title(f'Historical {data_map[table]} Fuel Mix - Daily Averages by Weekday', fontsize=16)
            plt.xlabel('Weekday', fontsize=12)
            plt.ylabel('Total Energy Generation (MW)', fontsize=12)

            plt.xticks(range(0, 7), ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
            plt.xlim([0, 6])
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')

            plt.grid(True)
            plt.tight_layout()
        elif 'caiso' in table:
            for fuel_source in caiso_fuel_sources:
                plt.bar(weekday_avg_overall.index,
                    weekday_avg_overall[fuel_source],
                    bottom=bottoms,
                    label=fuel_source,
                    color=cm.get_cmap('tab20c', len(caiso_fuel_sources))(caiso_fuel_sources.index(fuel_source)),
                    alpha=0.7)
                bottoms = [bottom + value for bottom, value in zip(bottoms, weekday_avg_overall[fuel_source])]

            plt.title(f'Historical {data_map[table]} Fuel Mix - Daily Averages by Weekday', fontsize=16)
            plt.xlabel('Weekday', fontsize=12)
            plt.ylabel('Total Energy Generation (MW)', fontsize=12)

            plt.xticks(range(0, 7), ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
            plt.xlim([0, 6])
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')

            plt.grid(True)
            plt.tight_layout()
        elif 'isone' in table:
            for fuel_source in isone_fuel_sources:
                plt.bar(weekday_avg_overall.index,
                    weekday_avg_overall[fuel_source],
                    bottom=bottoms,
                    label=fuel_source,
                    color=cm.get_cmap('tab20c', len(isone_fuel_sources))(isone_fuel_sources.index(fuel_source)),
                    alpha=0.7)
                bottoms = [bottom + value for bottom, value in zip(bottoms, weekday_avg_overall[fuel_source])]

            plt.title(f'Historical {data_map[table]} Fuel Mix - Daily Averages by Weekday', fontsize=16)
            plt.xlabel('Weekday', fontsize=12)
            plt.ylabel('Total Energy Generation (MW)', fontsize=12)

            plt.xticks(range(0, 7), ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
            plt.xlim([0, 6])
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')

            plt.grid(True)
            plt.tight_layout()        
    return fig

@st.cache_resource
def plot_daily_table_based_on_timerange(timemin, timemax, table):
    data = load_table_based_on_timerange(timemin, timemax, table)
    
    if 'load' in table:
        data_type = 'load'
    else:
        data_type = 'fuel_mix'

    data_copy = data.copy()

    data_copy['time'] = pd.to_datetime(data_copy['time'])
    data_copy.set_index('time', inplace=True)

    data_copy['Year'] = data_copy.index.year
    data_copy['Hour'] = data_copy.index.hour

    hourly_avg_per_year = data_copy.groupby(['Year', 'Hour']).mean().unstack(level=0)
    hourly_avg_overall = data_copy.groupby('Hour').mean()

    bottoms = [0] * len(hourly_avg_overall)

    fig = plt.figure(figsize=(12, 7))
    if data_type == "load":
        for year in data_copy['Year'].unique():
            hourly_data = hourly_avg_per_year['load'][year]
            plt.plot(hourly_data.index, hourly_data, alpha=0.3, label=str(year))


        plt.plot(hourly_avg_overall.index, hourly_avg_overall['load'], color='blue', linewidth=3, label='Average Load')


        plt.title(f'Historical {data_map[table]} Load Data - Hourly Averages', fontsize=16)
        plt.xlabel('Hour of Day', fontsize=12)
        plt.ylabel('Load (MW)', fontsize=12)


        plt.xticks(range(0, 24), [f'{i}:00' for i in range(0, 24)])
        plt.xlim([0, 23])

        plt.legend(title='Year', loc='upper right', bbox_to_anchor=(1.05, 1))
        plt.grid(True)
        plt.tight_layout()
    elif data_type == "fuel_mix":
        if 'nyiso' in table:
            for fuel_source in nyiso_fuel_sources:
                plt.bar(hourly_avg_overall.index,
                    hourly_avg_overall[fuel_source],
                    bottom=bottoms,
                    label=fuel_source,
                    color=cm.get_cmap('tab20c', len(nyiso_fuel_sources))(nyiso_fuel_sources.index(fuel_source)),
                    alpha=0.7)
                bottoms = [bottom + value for bottom, value in zip(bottoms, hourly_avg_overall[fuel_source])]

            plt.title(f'Historical {data_map[table]} Fuel Mix - Hourly Averages', fontsize=16)
            plt.xlabel('Hour of Day', fontsize=12)
            plt.ylabel('Total Energy Generation (MW)', fontsize=12)

            plt.xticks(range(0, 24), [f'{i}:00' for i in range(0, 24)])
            plt.xlim([0, 23])
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')

            plt.grid(True)
            plt.tight_layout()
        elif 'caiso' in table:
            for fuel_source in caiso_fuel_sources:
                plt.bar(hourly_avg_overall.index,
                    hourly_avg_overall[fuel_source],
                    bottom=bottoms,
                    label=fuel_source,
                    color=cm.get_cmap('tab20c', len(caiso_fuel_sources))(caiso_fuel_sources.index(fuel_source)),
                    alpha=0.7)
                bottoms = [bottom + value for bottom, value in zip(bottoms, hourly_avg_overall[fuel_source])]

            plt.title(f'Historical {data_map[table]} Fuel Mix - Hourly Averages', fontsize=16)
            plt.xlabel('Hour of Day', fontsize=12)
            plt.ylabel('Total Energy Generation (MW)', fontsize=12)

            plt.xticks(range(0, 24), [f'{i}:00' for i in range(0, 24)])
            plt.xlim([0, 23])
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')

            plt.grid(True)
            plt.tight_layout()
        elif 'isone' in table:
            for fuel_source in isone_fuel_sources:
                plt.bar(hourly_avg_overall.index,
                    hourly_avg_overall[fuel_source],
                    bottom=bottoms,
                    label=fuel_source,
                    color=cm.get_cmap('tab20c', len(isone_fuel_sources))(isone_fuel_sources.index(fuel_source)),
                    alpha=0.7)
                bottoms = [bottom + value for bottom, value in zip(bottoms, hourly_avg_overall[fuel_source])]

            plt.title(f'Historical {data_map[table]} Fuel Mix - Hourly Averages', fontsize=16)
            plt.xlabel('Hour of Day', fontsize=12)
            plt.ylabel('Total Energy Generation (MW)', fontsize=12)

            plt.xticks(range(0, 24), [f'{i}:00' for i in range(0, 24)])
            plt.xlim([0, 23])
            plt.legend(title="Energy Sources", bbox_to_anchor=(1.05, 1), loc='upper right')

            plt.grid(True)
            plt.tight_layout()        
    return fig

#nyiso_load = load_table_based_on_timerange('2019-01-01', None, 'nyiso_load')

#nyiso_load = conn.query('SELECT * FROM nyiso_load WHERE time >= \'2019-01-01\';', ttl="10m")



st.header('Exploratory Data Analysis', divider='gray')

st.write(
    "These are EDA plots. You can choose the timerange you want to explore."
)

#st.subheader("NYISO")

nyiso_eda_tab, caiso_eda_tab, isone_eda_tab = st.tabs(["NYISO", "CAISO", "ISONE"])

@st.fragment()
def trigger_nyiso_replots():
        with col1:
            fig1 = plot_monthly_table_based_on_timerange(nyiso_load_min_time_filter, nyiso_load_max_time_filter, 'nyiso_load')
            fig2 = plot_weekly_table_based_on_timerange(nyiso_load_min_time_filter, nyiso_load_max_time_filter, 'nyiso_load')
            fig3 = plot_daily_table_based_on_timerange(nyiso_load_min_time_filter, nyiso_load_max_time_filter, 'nyiso_load')

            plot_monthly_placeholder.pyplot(fig1)

            plot_weekly_placeholder.pyplot(fig2)

            plot_daily_placeholder.pyplot(fig3)

        
        with col2:
            fig4 = plot_monthly_table_based_on_timerange(nyiso_fuel_mix_min_time_filter, nyiso_fuel_mix_max_time_filter, 'nyiso_fuel_mix')
            fig5 = plot_weekly_table_based_on_timerange(nyiso_fuel_mix_min_time_filter, nyiso_fuel_mix_max_time_filter, 'nyiso_fuel_mix')
            fig6 = plot_daily_table_based_on_timerange(nyiso_fuel_mix_min_time_filter, nyiso_fuel_mix_max_time_filter, 'nyiso_fuel_mix')

            plot_monthly_fuel_mix_placeholder.pyplot(fig4)

            plot_weekly_fuel_mix_placeholder.pyplot(fig5)

            plot_daily_fuel_mix_placeholder.pyplot(fig6)


@st.fragment()
def trigger_caiso_replots():
        with col1:
            fig1 = plot_monthly_table_based_on_timerange(caiso_load_min_time_filter, caiso_load_max_time_filter, 'caiso_load')
            fig2 = plot_weekly_table_based_on_timerange(caiso_load_min_time_filter, caiso_load_max_time_filter, 'caiso_load')
            fig3 = plot_daily_table_based_on_timerange(caiso_load_min_time_filter, caiso_load_max_time_filter, 'caiso_load')

            plot_monthly_placeholder.pyplot(fig1)

            plot_weekly_placeholder.pyplot(fig2)

            plot_daily_placeholder.pyplot(fig3)

        
        with col2:
            fig4 = plot_monthly_table_based_on_timerange(caiso_fuel_mix_min_time_filter, caiso_fuel_mix_max_time_filter, 'caiso_fuel_mix')
            fig5 = plot_weekly_table_based_on_timerange(caiso_fuel_mix_min_time_filter, caiso_fuel_mix_max_time_filter, 'caiso_fuel_mix')
            fig6 = plot_daily_table_based_on_timerange(caiso_fuel_mix_min_time_filter, caiso_fuel_mix_max_time_filter, 'caiso_fuel_mix')

            plot_monthly_fuel_mix_placeholder.pyplot(fig4)

            plot_weekly_fuel_mix_placeholder.pyplot(fig5)

            plot_daily_fuel_mix_placeholder.pyplot(fig6)

def trigger_isone_replots():
        with col1:
            fig1 = plot_monthly_table_based_on_timerange(isone_load_min_time_filter, isone_load_max_time_filter, 'isone_load')
            fig2 = plot_weekly_table_based_on_timerange(isone_load_min_time_filter, isone_load_max_time_filter, 'isone_load')
            fig3 = plot_daily_table_based_on_timerange(isone_load_min_time_filter, isone_load_max_time_filter, 'isone_load')

            plot_monthly_placeholder.pyplot(fig1)

            plot_weekly_placeholder.pyplot(fig2)

            plot_daily_placeholder.pyplot(fig3)

        
        with col2:
            fig4 = plot_monthly_table_based_on_timerange(isone_fuel_mix_min_time_filter, isone_fuel_mix_max_time_filter, 'isone_fuel_mix')
            fig5 = plot_weekly_table_based_on_timerange(isone_fuel_mix_min_time_filter, isone_fuel_mix_max_time_filter, 'isone_fuel_mix')
            fig6 = plot_daily_table_based_on_timerange(isone_fuel_mix_min_time_filter, isone_fuel_mix_max_time_filter, 'isone_fuel_mix')

            plot_monthly_fuel_mix_placeholder.pyplot(fig4)

            plot_weekly_fuel_mix_placeholder.pyplot(fig5)

            plot_daily_fuel_mix_placeholder.pyplot(fig6)



with nyiso_eda_tab:
    st.write("EDA plots for NYISO.")

    col1, col2 = st.columns(2, vertical_alignment = "center")

    with col1:
        nyiso_load_min_time_filter = st.date_input("Start date:", 
                                            value=pd.to_datetime('2021-01-01'), 
                                            min_value=pd.to_datetime('2002-01-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_nyiso_replots,
                                            key='nyiso_load_min')
        nyiso_load_max_time_filter = st.date_input("End date:", 
                                            value=datetime.date.today(), 
                                            min_value=pd.to_datetime('2002-01-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_nyiso_replots,
                                            key='nyiso_load_max')
        plot_monthly_placeholder = st.empty()
        plot_weekly_placeholder = st.empty()
        plot_daily_placeholder = st.empty() 
        plot_monthly_placeholder.pyplot(plot_monthly_table_based_on_timerange(nyiso_load_min_time_filter, nyiso_load_max_time_filter, 'nyiso_load'))
        plot_weekly_placeholder.pyplot(plot_weekly_table_based_on_timerange(nyiso_load_min_time_filter, nyiso_load_max_time_filter, 'nyiso_load'))
        plot_daily_placeholder.pyplot(plot_daily_table_based_on_timerange(nyiso_load_min_time_filter, nyiso_load_max_time_filter, 'nyiso_load'))

    with col2:
        nyiso_fuel_mix_min_time_filter = st.date_input("Start date:", 
                                            value=pd.to_datetime('2021-01-01'), 
                                            min_value=pd.to_datetime('2018-01-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_nyiso_replots,
                                            key='nyiso_fuel_mix_min')
        nyiso_fuel_mix_max_time_filter = st.date_input("End date:", 
                                            value=datetime.date.today(), 
                                            min_value=pd.to_datetime('2002-01-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_nyiso_replots,
                                            key='nyiso_fuel_mix_max')

        plot_monthly_fuel_mix_placeholder = st.empty()
        plot_weekly_fuel_mix_placeholder = st.empty()
        plot_daily_fuel_mix_placeholder = st.empty()
        plot_monthly_fuel_mix_placeholder.pyplot(plot_monthly_table_based_on_timerange(nyiso_fuel_mix_min_time_filter, nyiso_fuel_mix_max_time_filter, 'nyiso_fuel_mix'))
        plot_weekly_fuel_mix_placeholder.pyplot(plot_weekly_table_based_on_timerange(nyiso_fuel_mix_min_time_filter, nyiso_fuel_mix_max_time_filter, 'nyiso_fuel_mix'))
        plot_daily_fuel_mix_placeholder.pyplot(plot_daily_table_based_on_timerange(nyiso_fuel_mix_min_time_filter, nyiso_fuel_mix_max_time_filter, 'nyiso_fuel_mix'))

with caiso_eda_tab:
    st.write("EDA plots for CAISO.")

    col1, col2 = st.columns(2, vertical_alignment = "center")

    with col1:
        caiso_load_min_time_filter = st.date_input("Start date:", 
                                            value=pd.to_datetime('2021-01-01'), 
                                            min_value=pd.to_datetime('2002-01-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_caiso_replots,
                                            key='caiso_load_min')
        caiso_load_max_time_filter = st.date_input("End date:", 
                                            value=datetime.date.today(), 
                                            min_value=pd.to_datetime('2002-01-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_caiso_replots,
                                            key='caiso_load_max')
        plot_monthly_placeholder = st.empty()
        plot_weekly_placeholder = st.empty()
        plot_daily_placeholder = st.empty() 
        plot_monthly_placeholder.pyplot(plot_monthly_table_based_on_timerange(caiso_load_min_time_filter, caiso_load_max_time_filter, 'caiso_load'))
        plot_weekly_placeholder.pyplot(plot_weekly_table_based_on_timerange(caiso_load_min_time_filter, caiso_load_max_time_filter, 'caiso_load'))
        plot_daily_placeholder.pyplot(plot_daily_table_based_on_timerange(caiso_load_min_time_filter, caiso_load_max_time_filter, 'caiso_load'))

    with col2:
        caiso_fuel_mix_min_time_filter = st.date_input("Start date:", 
                                            value=pd.to_datetime('2021-01-01'), 
                                            min_value=pd.to_datetime('2019-01-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_caiso_replots,
                                            key='caiso_fuel_mix_min')
        caiso_fuel_mix_max_time_filter = st.date_input("End date:", 
                                            value=datetime.date.today(), 
                                            min_value=pd.to_datetime('2019-01-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_caiso_replots,
                                            key='caiso_fuel_mix_max')

        plot_monthly_fuel_mix_placeholder = st.empty()
        plot_weekly_fuel_mix_placeholder = st.empty()
        plot_daily_fuel_mix_placeholder = st.empty()
        plot_monthly_fuel_mix_placeholder.pyplot(plot_monthly_table_based_on_timerange(caiso_fuel_mix_min_time_filter, caiso_fuel_mix_max_time_filter, 'caiso_fuel_mix'))
        plot_weekly_fuel_mix_placeholder.pyplot(plot_weekly_table_based_on_timerange(caiso_fuel_mix_min_time_filter, caiso_fuel_mix_max_time_filter, 'caiso_fuel_mix'))
        plot_daily_fuel_mix_placeholder.pyplot(plot_daily_table_based_on_timerange(caiso_fuel_mix_min_time_filter, caiso_fuel_mix_max_time_filter, 'caiso_fuel_mix'))

with isone_eda_tab:
    st.write("EDA plots for ISONE.")

    col1, col2 = st.columns(2, vertical_alignment = "center")

    with col1:
        isone_load_min_time_filter = st.date_input("Start date:", 
                                            value=pd.to_datetime('2023-01-01'), 
                                            min_value=pd.to_datetime('2022-07-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_isone_replots,
                                            key='isone_load_min')
        isone_load_max_time_filter = st.date_input("End date:", 
                                            value=datetime.date.today(), 
                                            min_value=pd.to_datetime('2022-07-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_isone_replots,
                                            key='isone_load_max')
        plot_monthly_placeholder = st.empty()
        plot_weekly_placeholder = st.empty()
        plot_daily_placeholder = st.empty() 
        plot_monthly_placeholder.pyplot(plot_monthly_table_based_on_timerange(isone_load_min_time_filter, isone_load_max_time_filter, 'isone_load'))
        plot_weekly_placeholder.pyplot(plot_weekly_table_based_on_timerange(isone_load_min_time_filter, isone_load_max_time_filter, 'isone_load'))
        plot_daily_placeholder.pyplot(plot_daily_table_based_on_timerange(isone_load_min_time_filter, isone_load_max_time_filter, 'isone_load'))

    with col2:
        isone_fuel_mix_min_time_filter = st.date_input("Start date:", 
                                            value=pd.to_datetime('2021-01-01'), 
                                            min_value=pd.to_datetime('2018-01-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_isone_replots,
                                            key='isone_fuel_mix_min')
        isone_fuel_mix_max_time_filter = st.date_input("End date:", 
                                            value=datetime.date.today(), 
                                            min_value=pd.to_datetime('2018-01-01'), 
                                            max_value=datetime.date.today(),
                                            on_change=trigger_isone_replots,
                                            key='isone_fuel_mix_max')

        plot_monthly_fuel_mix_placeholder = st.empty()
        plot_weekly_fuel_mix_placeholder = st.empty()
        plot_daily_fuel_mix_placeholder = st.empty()
        plot_monthly_fuel_mix_placeholder.pyplot(plot_monthly_table_based_on_timerange(isone_fuel_mix_min_time_filter, isone_fuel_mix_max_time_filter, 'isone_fuel_mix'))
        plot_weekly_fuel_mix_placeholder.pyplot(plot_weekly_table_based_on_timerange(isone_fuel_mix_min_time_filter, isone_fuel_mix_max_time_filter, 'isone_fuel_mix'))
        plot_daily_fuel_mix_placeholder.pyplot(plot_daily_table_based_on_timerange(isone_fuel_mix_min_time_filter, isone_fuel_mix_max_time_filter, 'isone_fuel_mix'))

    