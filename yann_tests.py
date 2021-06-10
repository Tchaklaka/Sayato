# coding: utf-8

#%%

from threading import currentThread
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

paris = capitals.set_index('CapitalName').loc['Paris',:]
lat = paris['CapitalLatitude']
lon = paris['CapitalLongitude']

capitals.head()

#%%

def get_api_key():
    config = configparser.ConfigParser()
    config.read("config.ini")

    return config['openweathermap']['api']

def get_current_weather_results(weather_dict):
    current = pd.Series(weather_dict['current'])
    current['dt'] = dt.datetime.fromtimestamp(current['dt'])
    current['sunrise'] = dt.datetime.fromtimestamp(current['sunrise'])
    current['sunset'] = dt.datetime.fromtimestamp(current['sunset'])
    current['weather_condition'] = current['weather'][0]['main']
    current['weather_icon'] = current['weather'][0]['icon']
    current.drop(['weather'], inplace=True)

    return current

def get_hourly_weather_results(weather_dict):
    hourly = pd.DataFrame(weather_dict['hourly'])
    hourly.loc[:,'weather_condition'] = hourly['weather'].map(lambda ls: ls[0]['main'])
    hourly.loc[:,'weather_icon'] = hourly['weather'].map(lambda ls: ls[0]['icon'])
    hourly.drop(columns=['weather'], inplace=True)
    hourly.loc[:,'dt'] = hourly['dt'].map(dt.datetime.fromtimestamp)
    
    return hourly

def get_weather_results(lat, lon):
    # , previous_weather_dict
    api_key = get_api_key()
    url = base_url.format(lat, lon, api_key)
    response = json.loads(requests.get(url).text)
    if response.get('cod') and response.get('cod') == 429:
        # if previous_weather_dict:
        #     weather_dict = previous_weather_dict
        # else:
        raise Exception("Compte OpenWeather bloqué et pas de dictionnaire par défaut")
    else:
        weather_dict = response
    # weather_dict['timezone']
    current = get_current_weather_results(weather_dict)
    hourly = get_hourly_weather_results(weather_dict)

    return current, hourly

current, hourly = get_weather_results(lat, lon)

pp.pprint(current)
hourly.head()

#%%

# https://plotly.com/python/mapbox-layers/

import plotly.express as px

weather_tile_base_url = "https://tile.openweathermap.org/map/{}/{}/{}/{}.png?appid={}"

def update_map(layer, capitals_df):
    weather_tile_url = weather_tile_base_url.format(layer, "{z}", "{x}", "{y}", get_api_key())
    fig = px.scatter_mapbox(
        capitals_df,
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

    return fig

layers = ["clouds_new", "precipitation_new", "pressure_new", "wind_new", "temp_new"]

fig = update_map(layers[-1], capitals)
# fig.show()

#%%

from bson import json_util

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

app.layout = html.Div([
    dcc.Graph(
        id='mapmonde',
        figure=fig
    ),

    dcc.Interval(
        id='interval-component',
        interval=10 * 1000, # in milliseconds
        n_intervals=0
    ),
    
    dcc.Store(id='capitale'),
    
    dcc.Store(id='current'),
    
    dcc.Store(id='hourly'),
    
    html.Div(className='row', children=[
        html.Div([
            dcc.Markdown("""
                **Test**
            """),
            html.Pre(id='test', style=styles['pre']),
        ], className='three columns')
    ]),
])

@app.callback(
    Output('test', 'children'),
    [
        Input('capitale', 'data'),
        Input('current', 'data'),
        Input('hourly', 'data')
    ]
)
def test_interactions(capitale_data, current, hourly):
    capitale_data = json.loads(capitale_data, object_hook=json_util.object_hook)
    current = json.loads(current, object_hook=json_util.object_hook)
    hourly = json.loads(hourly, object_hook=json_util.object_hook)
    test = json.dumps(
        {'capitale': capitale_data, 'current': current, 'hourly': hourly},
        default=json_util.default,
        indent=2
    )

    return test

@app.callback(
    [
        Output('current', 'data'),
        Output('hourly', 'data')
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('capitale', 'data')
    ]
)
def stream_data(n_intervals, capitale_data):
    capitale_data = json.loads(capitale_data)
    current, hourly = get_weather_results(
        capitale_data['CapitalLatitude'],
        capitale_data['CapitalLongitude']
    )
    current = current.to_json(date_format='iso', orient='index')
    hourly = hourly.to_json(date_format='iso', orient='records')

    return current, hourly

@app.callback(
    Output('capitale', 'data'),
    Input('mapmonde', 'clickData')
)
def display_click_data(capitale_data):
    if capitale_data:
        capital_name = capitale_data['points'][0]['hovertext']
        capitale_data = capitals.set_index('CapitalName').loc[capital_name,:].to_dict()
        capitale_data['CapitalName'] = capital_name
    else:
        capitale_data = capitals.iloc[0].to_dict()

    return json.dumps(capitale_data)


if __name__ == '__main__':
    app.run_server(debug=True)

#%%
