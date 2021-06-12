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
from plotly.subplots import make_subplots
import plotly.graph_objects as go
pp = pprint.PrettyPrinter(indent=4, depth=2, compact=True)

# Paramètres globaux
layers = {
    "Nuages": "cloud_new",
    "Précipitations": "precipitation_new",
    "Pression": "pressure_new",
    "Vent": "wind_new",
    "Température": "temp_new"
}
init_layer = "temp_new"
scatter_mapbox_marker_color = "yellow"
scatter_mapbox_marker_color_selected = "red"

# URLs des APIs
one_call_api_base_url = "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&appid={}&units=metric"
weather_tile_api_base_url = "https://tile.openweathermap.org/map/{}/{}/{}/{}.png?appid={}"

# Ressource : liste des capitales mondiales avec leurs coordonnées
capitals = pd.read_csv("concap.csv").dropna().reset_index(drop=True)
#df = pd.read_csv("data_test/hourly.csv",index_col=0)
def get_api_key():
    """Obtention de la clé API d'OpenWeather"""

    config = configparser.ConfigParser()
    config.read("config.ini")

    return config['openweathermap']['api']

def get_current_weather_results(weather_dict):
    """Extraction des données currentes du dictionnaire des résultats météo global"""

    current = pd.Series(weather_dict['current'])
    current['dt'] = dt.datetime.fromtimestamp(current['dt'])
    current['sunrise'] = dt.datetime.fromtimestamp(current['sunrise'])
    current['sunset'] = dt.datetime.fromtimestamp(current['sunset'])
    current['weather_condition'] = current['weather'][0]['main']
    current['weather_icon'] = current['weather'][0]['icon']
    current.drop(['weather'], inplace=True)

    return current

def get_hourly_weather_results(weather_dict):
    """Extraction des données horaires prévisionnelles du dictionnaire des résultats météo global"""

    hourly = pd.DataFrame(weather_dict['hourly'])
    hourly.loc[:,'weather_condition'] = hourly['weather'].map(lambda ls: ls[0]['main'])
    hourly.loc[:,'weather_icon'] = hourly['weather'].map(lambda ls: ls[0]['icon'])
    hourly.drop(columns=['weather'], inplace=True)
    hourly.loc[:,'dt'] = hourly['dt'].map(dt.datetime.fromtimestamp)
    
    return hourly


#df=get_hourly_weather_results('capitale')
def get_weather_results(lat, lon):
    """Obtention des résultats météo currents et prévisionnels"""
    
    api_key = get_api_key()
    url = one_call_api_base_url.format(lat, lon, api_key)
    response = json.loads(requests.get(url).text)
    if response.get('cod') and response.get('cod') == 429:
        raise Exception("Compte OpenWeather bloqué et pas de dictionnaire par défaut")
    else:
        weather_dict = response
    current = get_current_weather_results(weather_dict)
    hourly = get_hourly_weather_results(weather_dict)

    return current, hourly

# https://plotly.com/python/mapbox-layers/

def color_capital_map(fig, capitale_data):
    """Colorie les points de la carte en différenciant celui correspondant à la capitale sélectionnée"""

    capitale_data = json.loads(capitale_data)
    colors = [scatter_mapbox_marker_color] * capitals.shape[0]
    capital_names = capitals.set_index('CapitalName').index
    clicked_capital_idx = capital_names.get_loc(capitale_data['CapitalName'])
    colors[clicked_capital_idx] = scatter_mapbox_marker_color_selected
    fig.update_traces(overwrite=True, marker={"color": colors})

    return fig

def load_tile_map(fig, selected_layer):
    """Charge les couches cartographiques de la carte, en fonction de l'information demandée par l'utilisateur"""

    weather_tile_url = weather_tile_api_base_url.format(selected_layer, "{z}", "{x}", "{y}", get_api_key())
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

def create_map(capitals_df):
    """Création de la carte : couche ESRI, couche météo et points correspondants aux villes"""

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
    load_tile_map(fig, init_layer)
    # possibilité d'utiliser USGSImageryTopo
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig

# Serveur
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

# Mise en page
app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H1("Bulletin météo de SAYATO")
                    ], className='col-9 bg-light'),
                    html.Div([
                        dcc.Graph(
                            id='indicateur'
                        )
                    ]),
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.Label("Carte", className="h4")
                                    ], className='col-12')
                                ], className='row'),

                                html.Div([
                                    html.Div([
                                        dcc.Dropdown(
                                            options=[{'label': key, 'value': val} for key, val in layers.items()],
                                            value=init_layer,
                                            clearable=False,
                                            id="layers-dropdown"
                                        )
                                    ], className='col-12')
                                ], className='row')
                            ], className='col-12')
                        ], className='row')
                    ], className='col-3 bg-info')
                ], className='row'),

                html.Div([
                    dcc.Graph(
                        id='mapmonde',
                        figure=create_map(capitals),
                        className="col-12 aspect-ratio-box-inside"
                    )
                ], className="row aspect-ratio-box bg-info"),
                html.Div([
                    dcc.Graph(
                        id='graphe'
                    )
                ]),
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H2("Test")
                            ], className='row'),

                            html.Div([
                                html.Pre(
                                    id='test',
                                    className="pre",
                                    style={"overflowX": "scroll"}
                            )], className='row')
                        ], className='container')
                    ], className='col-6'),

                    html.Div([
                    ], className='col-6')
                ], className='row bg-light')
            ], className='container')
        ], className="col-12")
    ], className="row"),

    html.Div([
        dcc.Interval(
            id='interval-component-300s',
            interval=300 * 1000,
            n_intervals=0
        ),

        dcc.Interval(
            id='interval-component-120s',
            interval=120 * 1000,
            n_intervals=0
        ),
        
        dcc.Store(id='capitale'),
        
        dcc.Store(id='current'),
        
        dcc.Store(id='hourly')
    ], className='row')
], className="container")



@app.callback(
    Output('test', 'children'),
    [
        Input('capitale', 'data'),
        Input('current', 'data'),
        Input('hourly', 'data')
    ]
)
def test_interactions(capitale_data, current, hourly):
    """Affichage des données sauvegardées sur le navigateur client à l'issu des différents callbacks"""

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
    Output('indicateur','figure'),
    Input('hourly','data')
)
def indicateur(hourly):
    fig = go.Figure()
    df = json.loads(hourly, object_hook=json_util.object_hook)
    df=pd.DataFrame(df)

    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode = "gauge+number",
        value = df.loc[(df["dt"]==df.iloc[0]['dt']),'humidity'].values[0],
        number = {'suffix': "%"},
        title = {'text': "Humidité"},
        gauge = {
            'axis': {'range': [None,100]}},
        domain = {'row': 0, 'column': 0}))

    fig.add_trace(go.Indicator(
        mode = "number+delta",
        value = df.loc[(df["dt"]==df.iloc[0]['dt']),'temp'].values[0],
        title = {'text': "Température actuelle"},
        number = {'suffix': "°C"},
        #domain = {'x': [0.05, 0.5], 'y': [0.15, 0.35]}))
        domain = {'row': 1, 'column': 0}))

    fig.add_trace(go.Indicator(
        mode = "number+delta",
        value = df.loc[(df["dt"]==df.iloc[0]['dt']),'wind_speed'].values[0],
        number = {'suffix': " Km/h"},
        title = {'text': "Vitesse du vent"},
        domain = {'row': 0, 'column': 1}))

    fig.add_trace(go.Indicator(
         mode = "number+delta",
        value = df.loc[(df["dt"]==df.iloc[0]['dt']),'temp'].values[0],
        title = {'text': "Ressenti"},
        number = {'suffix': "°C"},
        domain = {'row': 1, 'column': 1}))
    
    # Add images
    fig.add_layout_image(
            dict(
                source="assets/favicon.io",
                xref="x",
                yref="y",
                x=0,
                y=3,
                sizex=2,
                sizey=2,
                sizing="stretch",
                opacity=0.5,
                layer="below")
    )

    fig.update_layout(
        grid = {'rows': 2, 'columns': 2, 'pattern': "independent"},
        template = {'data' : {'indicator': [{
            'title': {'text': "Speed"},
            'mode' : "number+delta+gauge"}]
                            }})
    return fig

@app.callback(
    Output('graphe','figure'),
    Input('hourly','data')
)
def serie_temp_tab(hourly):
    df = json.loads(hourly, object_hook=json_util.object_hook)
    df=pd.DataFrame(df)
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
    return fig

@app.callback(
    [
        Output('current', 'data'),
        Output('hourly', 'data')
    ],
    [
        Input('interval-component-120s', 'n_intervals'),
        Input('capitale', 'data')
    ]
)
def stream_data(n_intervals, capitale_data):
    """Appels API récurrents pour obtenir les dernières données météo ponctuelles"""

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
def store_click_data(capitale_data):
    """Callback intermédiaire sauvegardant la ville cliquée sur le navigateur du client"""

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
        Input('interval-component-300s', 'n_intervals'),
        Input('layers-dropdown', 'value')
    ],
    State('mapmonde', 'figure')
)
def update_map(capitale_data, _, selected_layer, fig_json):
    """Mise à jour de la carte : coloration de la ville cliquée, et mise à jour de la couche météo selon les choix de l'utilisateur et un compteur d'intervalles"""

    fig = go.Figure(fig_json)
    color_capital_map(fig, capitale_data)
    load_tile_map(fig, selected_layer)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
