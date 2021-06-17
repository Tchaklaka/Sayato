# coding: utf-8

import locale

from components import client, figures
from components.app import app, application
from components.capitals import capitals
from components.config import api_key, weather_tile_api_base_url, layers, init_layer, \
    variables, init_variable, variables_quanti, scatter_mapbox_marker_color
from components.callbacks import *


# Format des dates français (si disponible)
locale.setlocale(locale.LC_TIME, "fr_FR")

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

# Lancement du serveur
if __name__ == '__main__':
    app.run_server(debug=True)
