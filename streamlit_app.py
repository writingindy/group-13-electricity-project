import streamlit as st
import pandas as pd
import warnings
import gridstatus
import psycopg2
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title='Electricity Data Dashboard',
    page_icon=':electric_plug:', # This is an emoji shortcode. Could be a URL too.
)


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


nyiso_load = load_table_based_on_timerange('2019-01-01', None, 'nyiso_load')

#nyiso_load = conn.query('SELECT * FROM nyiso_load WHERE time >= \'2019-01-01\';', ttl="10m")

st.header('Exploratory Data Analysis', divider='gray')

st.write(
    "This is a plot of the Monthly Average Electricity Load for NYISO"
)


import pandas as pd
import matplotlib.pyplot as plt

nyiso_load_copy = nyiso_load.copy()
nyiso_load_copy['time'] = pd.to_datetime(nyiso_load_copy['time'])
nyiso_load_copy.set_index('time', inplace=True)

daily_load = nyiso_load_copy.resample('D').mean()

nyiso_load_copy['Year'] = nyiso_load_copy.index.year
nyiso_load_copy['Month'] = nyiso_load_copy.index.month


monthly_load_avg_per_year = nyiso_load_copy.groupby(['Year', 'Month']).mean().unstack(level=0)
monthly_load_avg_overall = nyiso_load_copy.groupby('Month').mean()
fig = plt.figure(figsize=(12, 6))

for year in nyiso_load_copy['Year'].unique():
    monthly_data = monthly_load_avg_per_year['load'][year]
    plt.plot(monthly_data.index, monthly_data, alpha=0.3, label=str(year))

plt.plot(monthly_load_avg_overall.index, monthly_load_avg_overall['load'], color='blue', linewidth=3, label='Average Load')

plt.title('Historical New York Load Data - Monthly Averages')
plt.xlabel('Month')
plt.ylabel('Load (MW)')


plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
plt.xlim([1, 12])


plt.legend(title='Year', loc='upper right', bbox_to_anchor=(1.05, 1))
plt.grid(True)
plt.tight_layout()

st.pyplot(fig)

st.write(
    "This is a plot of the Daily Average Electricity Load for NYISO over the week"
)

#Weekly
daily_load = nyiso_load_copy.resample('D').mean()


nyiso_load_copy['Year'] = nyiso_load_copy.index.year
nyiso_load_copy['Weekday'] = nyiso_load_copy.index.weekday  # Monday=0, Sunday=6


weekday_load_avg_per_year = nyiso_load_copy.groupby(['Year', 'Weekday']).mean().unstack(level=0)
weekday_load_avg_overall = nyiso_load_copy.groupby('Weekday').mean()


fig2 = plt.figure(figsize=(12, 6))

for year in nyiso_load_copy['Year'].unique():
    weekday_data = weekday_load_avg_per_year['Load'][year]
    plt.plot(weekday_data.index, weekday_data, alpha=0.3, label=str(year))


plt.plot(weekday_load_avg_overall.index, weekday_load_avg_overall['load'], color='blue', linewidth=3, label='Average Load')


plt.title('Historical New York Load Data - Daily Averages by Weekday')
plt.xlabel('Weekday')
plt.ylabel('Load (MW)')


plt.xticks(range(0, 7), ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
plt.xlim([0, 6])

plt.legend(title='Year', loc='upper right', bbox_to_anchor=(1.05, 1))
plt.grid(True)
plt.tight_layout()
st.pyplot(fig2)