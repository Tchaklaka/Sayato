# coding: utf-8

import json

from babel.dates import format_datetime
from bson import json_util
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go

from .api import get_weather_results
from .app import app
from .capitals import capitals
from .config import api_key, one_call_api_base_url, weather_tile_api_base_url, datetime_label, variables, \
    scatter_mapbox_marker_color, scatter_mapbox_marker_color_selected
from .figures import color_capital_map, create_indicateur, create_serie_temp, create_table, load_tile_map


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
    color_capital_map(
        fig,
        capitale_data['CapitalName'],
        capitals,
        marker_color=scatter_mapbox_marker_color,
        marker_color_selected=scatter_mapbox_marker_color_selected
    )
    load_tile_map(fig, selected_layer, weather_tile_api_base_url, api_key)

    return fig

@app.callback(
    Output('indicateur','figure'),
    Input('current','data')
)
def indicateur(current):
    """Mise à jour des indicateurs pour les données courantes"""

    series_current = pd.Series(json.loads(current, object_hook=json_util.object_hook))

    return create_indicateur(series_current)

@app.callback(
    Output('graphe-serie','figure'),
    [
        Input('hourly','data'),
        Input('variables-prevision-dropdown', 'value')
    ]
)
def serie_temp(hourly, variable_selected):
    """Mise à jour du graphique des prévisions pour la variable sélectionnée"""

    hourly_df = pd.DataFrame(json.loads(hourly, object_hook=json_util.object_hook))
    hourly_df.loc[:,'dt'] = pd.to_datetime(hourly_df['dt'])

    variable_label = {v: k for k, v in variables.items()}[variable_selected]

    return create_serie_temp(hourly_df, variable_selected, variable_label)

@app.callback(
    Output('tab', 'figure'),
    Input('hourly','data')
)
def tab(hourly):
    """Mise à jour du tableau des prévisions"""

    hourly_df = pd.DataFrame(json.loads(hourly, object_hook=json_util.object_hook))
    hourly_df.loc[:,'dt'] = pd.to_datetime(hourly_df['dt'])
    hourly_df.loc[:,'dt'] = hourly_df['dt'].apply(lambda d: format_datetime(d, "EEE H", locale="fr")) + "h"

    return create_table(hourly_df, datetime_label, variables)
