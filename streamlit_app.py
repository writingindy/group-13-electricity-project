import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import warnings
import plotly.express as px
import gridstatus
import datetime
import time
import psycopg2
from st_pages import add_page_title, get_nav_from_toml

warnings.filterwarnings('ignore')

st.set_page_config(
    #layout="wide",
    page_title='Electricity Data Dashboard',
    page_icon=':electric_plug:', # This is an emoji shortcode. Could be a URL too.
)


# If you want to use the no-sections version, this
# defaults to looking in .streamlit/pages.toml, so you can
# just call `get_nav_from_toml()`
#nav = get_nav_from_toml(".streamlit/pages_sections.toml")


#pg = st.navigation(nav)

#add_page_title(pg)



st.title("Electricity Data Dashboard")


'''
This web app will present some exploratory data analysis on electricity data, gathered from the gridstatus API.
'''

@st.cache_data
def get_day_data(table) -> pd.DataFrame:
    today = str(datetime.date.today())

    conn = st.connection("postgresql", type="sql")
    
    res = conn.query(f"SELECT * FROM {table} WHERE time >= \'{today}\';", ttl="10m")

    return res

#today_nyiso_load = get_day_data('nyiso_load')

placeholder = st.empty()

#with placeholder.container():

    # create three columns
#    nyiso_load, caiso_load, isone_load = st.columns(3)

    # fill in those three columns with respective metrics or KPIs
    #kpi1.metric(
    #    label="Age ⏳",
    #    value=round(avg_age),
    #    delta=round(avg_age) - 10,
    #)
    
    #kpi2.metric(
    #    label="Married Count 💍",
    #    value=int(count_married),
    #    delta=-10 + count_married,
    #)
    
    #kpi3.metric(
    #    label="A/C Balance ＄",
    #    value=f"$ {round(balance,2)} ",
    #    delta=-round(balance / count_married) * 100,
    #)

    # create two columns for charts
#    fig_col1, fig_col2 = st.columns(2)
    
#    with fig_col1:
#        st.markdown("### First Chart")
    #    fig = px.density_heatmap(
    #        data_frame=df, y="age_new", x="marital"
    #    )
    #    st.write(fig)
        
#    with fig_col2:
#        st.markdown("### Second Chart")
    #    fig2 = px.histogram(data_frame=df, x="age_new")
    #    st.write(fig2)

#    st.markdown("### Detailed Data View")
    #st.dataframe(df)
    #time.sleep(1)


    
    #return pd.read_csv(dataset_url)

@st.cache_data
def load_table_based_on_timerange(timemin, timemax, table):
    
    conn = st.connection("postgresql", type="sql")
    if timemax is None:
        res = conn.query(f"SELECT * FROM {table} WHERE time >= \'{timemin}\';", ttl="10m")
    else:
        res = conn.query(f"SELECT * FROM {table} WHERE time >= \'{timemin}\' AND time < \'{timemax}\';", ttl="10m")
    
    return res

def plot_table_based_on_timerange(timemin, timemax, table):
    data = load_table_based_on_timerange(timemin, timemax, table)

    data_map = {'nyiso_load': 'New York', 
                'nyiso_fuel_mix': 'New York',
                'caiso_load': 'California',
                'caiso_fuel_mix': 'California',
                'isone_load': 'New England',
                'isone_fuel_mix': 'New England'}

    data_copy = data.copy()

    data_copy['time'] = pd.to_datetime(data_copy['time'])
    data_copy.set_index('time', inplace=True)

    daily_data = data_copy.resample('D').mean()

    data_copy['Year'] = data_copy.index.year
    data_copy['Month'] = data_copy.index.month

    monthly_avg_per_year = data_copy.groupby(['Year', 'Month']).mean().unstack(level=0)
    monthly_avg_overall = data_copy.groupby('Month').mean()

    fig = plt.figure(figsize=(12, 6))

    for year in data_copy['Year'].unique():
        monthly = monthly_avg_per_year['load'][year]
        plt.plot(monthly.index, monthly, alpha=0.3, label=str(year))

    plt.plot(monthly_avg_overall.index, monthly_avg_overall['load'], color='blue', linewidth=3, label='Average Load')
    plt.title(f'Historical {data_map[table]} Load Data - Monthly Averages')
    plt.xlabel('Month')
    plt.ylabel('Load (MW)')

    plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    plt.xlim([1, 12])

    plt.legend(title='Year', loc='upper right', bbox_to_anchor=(1.05, 1))
    plt.grid(True)
    plt.tight_layout()
    st.pyplot(fig)


nyiso_load = load_table_based_on_timerange('2019-01-01', None, 'nyiso_load')

#nyiso_load = conn.query('SELECT * FROM nyiso_load WHERE time >= \'2019-01-01\';', ttl="10m")

st.header('Exploratory Data Analysis', divider='gray')

st.write(
    "This is a plot of the Monthly Average Electricity Load for NYISO. You can choose the timerange you want to explore."
)






