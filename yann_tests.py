# coding: utf-8

#%%

import requests
import json
import datetime as dt
import pandas as pd
import pprint
import configparser

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
