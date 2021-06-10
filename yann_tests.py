# coding: utf-8

import json
import datetime as dt
import pandas as pd
import pprint
import configparser
from bson import json_util

import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import requests

pp = pprint.PrettyPrinter(indent=4, depth=2, compact=True)

layers = {
    "Nuages": "cloud_new",
    "Précipitations": "precipitation_new",
    "Pression": "pressure_new",
    "Vent": "wind_new",
    "Température": "temp_new"
}
layer = "temp_new"
scatter_mapbox_marker_color = "yellow"

one_call_api_base_url = "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&appid={}&units=metric"
weather_tile_api_base_url = "https://tile.openweathermap.org/map/{}/{}/{}/{}.png?appid={}"

capitals = pd.read_csv("concap.csv").dropna().reset_index(drop=True)

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
    url = one_call_api_base_url.format(lat, lon, api_key)
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

# https://plotly.com/python/mapbox-layers/

def load_tile_map(fig, layer):
    weather_tile_url = weather_tile_api_base_url.format(layer, "{z}", "{x}", "{y}", get_api_key())
    fig.update_layout(
        mapbox_style="white-bg",
        mapbox_layers=[
            {
                "below": "traces",
                "sourcetype": "raster",
                "sourceattribution": "ESRI",
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

    return fig

def create_map(layer, capitals_df):
    fig = px.scatter_mapbox(
        capitals_df,
        lat="CapitalLatitude",
        lon="CapitalLongitude",
        hover_name="CapitalName",
        hover_data={
            "CapitalName": True,
            "CountryName": True,
            "ContinentName": True,
            "CapitalLatitude": False,
            "CapitalLongitude": False
        },
        color_discrete_sequence=[scatter_mapbox_marker_color] * capitals_df.shape[0],
        zoom=1,
        height=600
    )
    fig.update_traces(hovertemplate="""
        <b>%{customdata[0]}</b>
        <br />
        <i>Country:</i> %{customdata[1]}
        <br />
        <i>Continent:</i> %{customdata[2]}
    """)
    load_tile_map(fig, layer)
    # possibilité d'utiliser USGSImageryTopo
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig

app = dash.Dash(
    __name__,
    assets_folder="assets",
    external_stylesheets=[
        "https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css"
    ],
    external_scripts=[
        "https://code.jquery.com/jquery-3.3.1.slim.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js",
        "https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js"
    ],
    title="Météo SAYATO",
    update_title="Rafraîchissement..."
)

app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div([
                                        html.Div(
                                            [
                                                html.H1("Bulletin météo de SAYATO")
                                            ],
                                            className='col-9 bg-light'
                                        ),
                                        
                                        html.Div(
                                            [
                                                # html.Div(
                                                #     [
                                                        html.Div(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        # html.Div(
                                                                        #     [
                                                                                html.Div(
                                                                                    [
                                                                                        html.Div(
                                                                                            [
                                                                                                html.Label("Carte", className="h4")
                                                                                            ],
                                                                                            className='col-12'
                                                                                        )
                                                                                    ],
                                                                                    className='row'
                                                                                ),

                                                                                html.Div(
                                                                                    [
                                                                                        html.Div(
                                                                                            [
                                                                                                dcc.Dropdown(
                                                                                                    options=[{'label': key, 'value': val} for key, val in layers.items()],
                                                                                                    value=layer,
                                                                                                    clearable=False,
                                                                                                    id="layers-dropdown"
                                                                                                )
                                                                                            ],
                                                                                            className='col-12'
                                                                                        )
                                                                                    ],
                                                                                    className='row'
                                                                                )
                                                                        #     ],
                                                                        #     className='container'
                                                                        # )
                                                                    ],
                                                                    className='col-12'
                                                                )
                                                            ],
                                                            className='row'
                                                        )
                                                #     ],
                                                #     className='container'
                                                # )
                                            ],
                                            className='col-3 bg-info'
                                        )
                                    ],
                                    className='row'
                                ),

                                html.Div(
                                    [
                                        dcc.Graph(
                                            id='mapmonde',
                                            figure=create_map(layer, capitals),
                                            className="col-12 aspect-ratio-box-inside"
                                        ),
                                    ],
                                    className="row aspect-ratio-box bg-info"
                                ),
                                
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Div(
                                                            [
                                                                html.H2("Test")
                                                            ],
                                                            className='row'
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.Pre(
                                                                    id='test',
                                                                    className="pre",
                                                                    style={"overflowX": "scroll"}
                                                                )
                                                            ],
                                                            className='row'
                                                        )
                                                    ],
                                                    className='container'
                                                )
                                            ], 
                                            className='col-6'
                                        ),
                                        html.Div(
                                            [],
                                            className='col-6'
                                        )
                                    ], 
                                    className='row bg-light'
                                )
                            ],
                            className='container'
                        )
                    ],
                    className="col-12"
                )
            ],
            className="row"
        ),

        html.Div(
            [
                dcc.Interval(
                    id='interval-component-60s',
                    interval=60 * 1000,
                    n_intervals=0
                ),

                dcc.Interval(
                    id='interval-component-10s',
                    interval=10 * 1000,
                    n_intervals=0
                ),
                
                dcc.Store(id='capitale'),
                
                dcc.Store(id='current'),
                
                dcc.Store(id='hourly')
            ],
            className='row'
        )
    ],
    className="container"
)

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
        Input('interval-component-10s', 'n_intervals'),
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

@app.callback(
    Output('mapmonde', 'figure'),
    [
        Input('capitale', 'data'),
        Input('interval-component-60s', 'n_intervals'),
        Input('layers-dropdown', 'value')
    ],
    State('mapmonde', 'figure')
)
def update_map(capitale_data, _, selected_layer, fig_json):
    fig = go.Figure(fig_json)

    capitale_data = json.loads(capitale_data)
    colors = [scatter_mapbox_marker_color] * capitals.shape[0]
    capital_names = capitals.set_index('CapitalName').index
    clicked_capital_idx = capital_names.get_loc(capitale_data['CapitalName'])
    colors[clicked_capital_idx] = "red"
    fig.update_traces(overwrite=True, marker={"color": colors})

    load_tile_map(fig, selected_layer)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
