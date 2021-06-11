# coding: utf-8

#%%

from pandas.core import series
import requests
import json
import datetime as dt
import pandas as pd
import pprint
import configparser

from requests.api import head

pp = pprint.PrettyPrinter(indent=4, depth=2, compact=True)

base_url = "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&appid={}&units=metric"

#%%

capitals = pd.read_csv("concap.csv").dropna()
capitals.set_index('CapitalName', inplace=True)

paris = capitals.loc['Paris',:]
lat = paris['CapitalLatitude']
lon = paris['CapitalLongitude']

capitals.head()

#%%

def get_api_key():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config['openweathermap']['api']

def get_weather_results(lat, lon):
    api_key = get_api_key()
    url = base_url.format(lat, lon, api_key)
    response = requests.get(url)
    return json.loads(response.text)

data = get_weather_results(lat, lon)
dt.timezone = data['timezone']
pp.pprint(data)

#%%

current = pd.Series(data['current'])
current['dt'] = dt.datetime.fromtimestamp(current['dt'])
current['sunrise'] = dt.datetime.fromtimestamp(current['sunrise'])
current['sunset'] = dt.datetime.fromtimestamp(current['sunset'])
current

#%%

hourly = pd.DataFrame(data['hourly'])
hourly.loc[:,'weather_condition'] = hourly['weather'].map(lambda ls: ls[0]['main'])
hourly.loc[:,'weather_icon'] = hourly['weather'].map(lambda ls: ls[0]['icon'])
hourly.drop(columns=['weather', 'rain'], inplace=True)
hourly.loc[:,'dt'] = hourly['dt'].map(dt.datetime.fromtimestamp)
hourly.head()


#%%

# https://plotly.com/python/mapbox-layers/

import plotly.express as px

weather_tile_base_url = "https://tile.openweathermap.org/map/{}/{}/{}/{}.png?appid={}"

layers = ["clouds_new", "precipitation_new", "pressure_new", "wind_new", "temp_new"]
weather_tile_url = weather_tile_base_url.format(layers[-1], "{z}", "{x}", "{y}", get_api_key())

fig = px.scatter_mapbox(
    capitals.reset_index(),
    lat="CapitalLatitude",
    lon="CapitalLongitude",
    hover_name="CapitalName",
    hover_data=["CountryName", "ContinentName"],
    color_discrete_sequence=["purple"],
    zoom=1,
    height=300
)
fig.update_layout(
    mapbox_style="white-bg",
    mapbox_layers=[
        {
            "below": "traces",
            "sourcetype": "raster",
            "sourceattribution": "United States Geological Survey",
            "source": [
                "https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}"
            ]
        },
        {
            "below": "traces",
            "sourcetype": "raster",
            "sourceattribution": "OpenWeather",
            "source": [weather_tile_url]
        }
    ]
)
# possibilité d'utiliser USGSImageryTopo
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig.show()

#%%
# Using graph_objects
import plotly.graph_objects as go

import pandas as pd
df = pd.read_csv("data_test/hourly.csv",index_col=0)
df=pd.DataFrame(df)
df.head()


# %%
import re
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    specs=[[{"type": "table"}],
          [{"secondary_y": True}]]
)

fig.add_trace(
    go.Scatter(
        x=df["dt"],
        y=df["temp"],
        mode="lines",
        name="température"
    ),
    row=2, col=1,secondary_y=False
)

fig.add_trace(
    go.Scatter(
        x=df["dt"],
        y=df["feels_like"],
        mode="lines",
        name="ressenti"
    ),
    row=2, col=1,secondary_y=True
)

fig.add_trace(
    go.Table(
        header=dict(
            values=["dt","temp","feels_like","pressure",
            "humidity","dew_point,uvi","clouds","visibility",
            "wind_speed","wind_deg","wind_gust","pop",
            "weather_condition","weather_icon"],
            font=dict(size=10),
            line_color='darkslategray',
            fill_color='paleturquoise',
            align="left"
        ),
        cells=dict(
            values=[df[k].tolist() for k in df.columns[0:]],
            line_color='darkslategray',
            fill_color='lavender',
            align = "left")
    ),
    row=1, col=1
)
fig.update_layout(
    height=900,
    width=900,
    showlegend=True,
    title_text="Température",
)

# Set x-axis title
fig.update_xaxes(title_text="Date")

# Set y-axes titles
fig.update_yaxes(title_text="Degre °C", secondary_y=False)
fig.update_yaxes(title_text="Degre °C", secondary_y=True)

fig.show()
# %%
import plotly.graph_objects as go

fig = go.Figure()

fig = go.Figure(go.Indicator(
    mode = "number+delta",
    #value = df.loc[df["dt"]=='2021-06-11T15:00:00.000Z','wind_speed'].values[0],
    value=df.iloc[0]['dt'],
    title = {'text': "Speed km/h"},
    domain = {'x': [0, 1], 'y': [0, 1]}
))

fig.show()
# %%
from datetime import datetime
from time import strftime
df.loc[(df["dt"]=='2021-06-10 09:00:00'),'feels_like']
#datetime.now().isoformat(sep=' ',timespec='seconds')
#df["dt"]
# %%
