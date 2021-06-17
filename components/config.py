# coding: utf-8

import configparser
import os


root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Lecture du fichier de configuration
config = configparser.ConfigParser()
config.read(os.path.join(root_dir, "config.ini"), encoding="utf-8")

# Stockage des paramètres globaux dans des variables
api_key = config['openweathermap']['api']
one_call_api_base_url = config['openweathermap']['one_call_api_base_url']
weather_tile_api_base_url = config['openweathermap']['weather_tile_api_base_url']
datetime_label = config['datetime_label']['datetime_label']
layers = {v: k for k, v in dict(config['layers']).items()}
init_layer = config['init_layer']['init_layer']
variables = {v: k for k, v in dict(config['variables']).items()}
variables_quanti = config['variables_quanti']['variables_quanti'].strip().split(sep="\n")
init_variable = config['init_variable']['init_variable']
scatter_mapbox_marker_color = config['scatter_mapbox_style']['marker_color']
scatter_mapbox_marker_color_selected = config['scatter_mapbox_style']['marker_color_selected']
