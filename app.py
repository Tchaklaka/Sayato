# coding: utf-8

import json
import datetime as dt
import pandas as pd
import configparser
import locale

from babel.dates import format_datetime
from bson import json_util
import plotly.graph_objects as go
import dash
from dash.dependencies import Input, Output, State

from components import client, figures, api


locale.setlocale(locale.LC_TIME, "fr_FR")

# Paramètres globaux
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")
api_key = config['openweathermap']['api']
one_call_api_base_url = config['openweathermap']['one_call_api_base_url']
weather_tile_api_base_url = config['openweathermap']['weather_tile_api_base_url']
layers = {v: k for k, v in dict(config['layers']).items()}
init_layer = config['init_layer']['init_layer']
datetime_label = config['datetime_label']['datetime_label']
variables = {v: k for k, v in dict(config['variables']).items()}
variables_quanti = config['variables_quanti']['variables_quanti'].strip().split(sep="\n")
init_variable = config['init_variable']['init_variable']
scatter_mapbox_marker_color = config['scatter_mapbox_style']['marker_color']
scatter_mapbox_marker_color_selected = config['scatter_mapbox_style']['marker_color_selected']

# Ressource : liste des capitales mondiales avec leurs coordonnées
capitals = pd.read_csv("data/concap.csv").dropna().reset_index(drop=True)

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
application = app.server

# Mise en page
init_map = figures.create_map(capitals, init_layer, weather_tile_api_base_url, api_key, scatter_mapbox_marker_color)
app.layout = client.generate_layout(
    layers=layers,
    variables=variables,
    init_layer=init_layer,
    init_variable=init_variable,
    variables_quanti=variables_quanti,
    init_map=init_map
)

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
    current, hourly = api.get_weather_results(
        capitale_data['CapitalLatitude'],
        capitale_data['CapitalLongitude'],
        one_call_api_base_url,
        api_key
    )
    current = current.to_json(date_format='iso', orient='index')
    hourly = hourly.to_json(date_format='iso', orient='records')

    return current, hourly

@app.callback(
    [
        Output('capitale', 'data'),
        Output('capitale-name', 'children')
    ],
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
        capital_name = capitale_data['CapitalName']

    return json.dumps(capitale_data), capital_name

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

    capitale_data = json.loads(capitale_data)

    fig = go.Figure(fig_json)
    figures.color_capital_map(
        fig,
        capitale_data['CapitalName'],
        capitals,
        marker_color=scatter_mapbox_marker_color,
        marker_color_selected=scatter_mapbox_marker_color_selected
    )
    figures.load_tile_map(fig, selected_layer, weather_tile_api_base_url, api_key)

    return fig

@app.callback(
    Output('indicateur','figure'),
    Input('current','data')
)
def indicateur(current):
    series_current = pd.Series(json.loads(current, object_hook=json_util.object_hook))

    return figures.create_indicateur(series_current)

@app.callback(
    Output('graphe-serie','figure'),
    [
        Input('hourly','data'),
        Input('variables-prevision-dropdown', 'value')
    ]
)
def serie_temp(hourly, variable_selected):
    hourly_df = pd.DataFrame(json.loads(hourly, object_hook=json_util.object_hook))
    hourly_df.loc[:,'dt'] = pd.to_datetime(hourly_df['dt'])

    variable_label = {v: k for k, v in variables.items()}[variable_selected]

    return figures.create_serie_temp(hourly_df, variable_selected, variable_label)

@app.callback(
    Output('tab', 'figure'),
    Input('hourly','data')
)
def tab(hourly):
    hourly_df = pd.DataFrame(json.loads(hourly, object_hook=json_util.object_hook))
    hourly_df.loc[:,'dt'] = pd.to_datetime(hourly_df['dt'])
    hourly_df.loc[:,'dt'] = hourly_df['dt'].apply(lambda d: format_datetime(d, "EEE H", locale="fr")) + "h"

    return figures.create_table(hourly_df, datetime_label, variables)

if __name__ == '__main__':
    app.run_server(debug=True)
