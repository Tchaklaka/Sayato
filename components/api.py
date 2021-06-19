# coding: utf-8

import datetime as dt
import json
import requests

import pandas as pd


def get_current_weather_results(weather_dict: dict):
    """Extraction des données currentes du dictionnaire des résultats météo global"""

    # Construction et mise en forme du DataFrame
    current = pd.Series(weather_dict['current'])
    current['dt'] = dt.datetime.fromtimestamp(current['dt'])
    current['sunrise'] = dt.datetime.fromtimestamp(current['sunrise'])
    current['sunset'] = dt.datetime.fromtimestamp(current['sunset'])
    current['weather_condition'] = current['weather'][0]['main']
    current['weather_icon'] = current['weather'][0]['icon']
    current.drop(['weather'], inplace=True)

    return current

def get_hourly_weather_results(weather_dict: dict):
    """Extraction des données horaires prévisionnelles du dictionnaire des résultats météo global"""

    # Construction et mise en forme du DataFrame
    hourly = pd.DataFrame(weather_dict['hourly'])
    hourly.loc[:,'weather_condition'] = hourly['weather'].map(lambda ls: ls[0]['main'])
    hourly.loc[:,'weather_icon'] = hourly['weather'].map(lambda ls: ls[0]['icon'])
    hourly.drop(columns=['weather'], inplace=True)
    hourly.loc[:,'dt'] = hourly['dt'].map(dt.datetime.fromtimestamp)
    
    return hourly

def get_weather_results(lat: float, lon: float, one_call_api_base_url: str, api_key: str):
    """Obtention des résultats météo currents et prévisionnels"""
    
    # Appel API
    url = one_call_api_base_url.format(lat, lon, api_key)
    response = json.loads(requests.get(url).text)

    # Lecture de la réponse, mise en forme des résultats en cas de succès
    if response.get('cod') and response.get('cod') == 429:
        raise Exception("Compte OpenWeather bloqué et pas de dictionnaire par défaut")
    else:
        weather_dict = response
    current = get_current_weather_results(weather_dict)
    hourly = get_hourly_weather_results(weather_dict)

    return current, hourly
