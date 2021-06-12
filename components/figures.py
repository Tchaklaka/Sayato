# coding: utf-8

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def color_capital_map(fig: go.Figure, selected_capital_name: dict[str, str], capitals_df: pd.DataFrame, marker_color: str="blue", marker_color_selected: str="red"):
    """Colorie les points de la carte en différenciant celui correspondant à la capitale sélectionnée"""

    colors = [marker_color] * capitals_df.shape[0]
    capital_names = capitals_df.set_index('CapitalName').index
    clicked_capital_idx = capital_names.get_loc(selected_capital_name)
    colors[clicked_capital_idx] = marker_color_selected
    fig.update_traces(overwrite=True, marker={"color": colors})

    return fig

def load_tile_map(fig: go.Figure, selected_layer: str, weather_tile_api_base_url:str, api_key:str):
    """Charge les couches cartographiques de la carte, en fonction de l'information demandée par l'utilisateur"""

    weather_tile_url = weather_tile_api_base_url.format(selected_layer, "{z}", "{x}", "{y}", api_key)
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

def create_map(capitals_df: pd.DataFrame, selected_layer: str, weather_tile_api_base_url:str, api_key:str, scatter_mapbox_marker_color: str="blue"):
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
    load_tile_map(fig, selected_layer, weather_tile_api_base_url, api_key)
    # possibilité d'utiliser USGSImageryTopo
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig

def create_indicateur(current: pd.Series):
    fig = go.Figure()

    # Jauge de température
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=current['humidity'],
        number={'suffix': " %"},
        title={'text': "Humidité"},
        gauge={'axis': {'range': [None, 100]}},
        domain={'row': 0, 'column': 0})
    )

    # Chiffre de la température mesurée
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current['temp'],
        title={'text': "Température mesurée"},
        number={'suffix': " °C"},
        domain={'row': 1, 'column': 0})
    )

    # Chiffre de la vitesse du vent
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current['wind_speed'],
        number={'suffix': " km/h"},
        title={'text': "Vitesse du vent"},
        domain={'row': 0, 'column': 1})
    )

    # Chiffre de la température ressentie
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=current['temp'],
        title={'text': "Température ressentie"},
        number={'suffix': " °C"},
        domain={'row': 1, 'column': 1})
    )

    fig.update_layout(
        grid={'rows': 2, 'columns': 2, 'pattern': "independent"},
        template={
            'data': {
                'indicator': [{
                    'title': {'text': "Speed"},
                    'mode': "number+delta+gauge"
                }]
            }
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=50, b=0)
    )

    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)

    return fig

def create_serie_temp(df: pd.DataFrame, variable_name: str, variable_label: str):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["dt"],
            y=df[variable_name],
            hovertemplate="""
                <i>Date et heure :</i> %{}
                <br />
                <i>{} :</i> %{} °C
            """.format("{x}", variable_label, "{y}")
        )
    )
    fig.update_layout(
        height=400,
        showlegend=False,
        margin={"r": 0, "t": 0, "l": 0, "b": 0, "pad": 1},
        paper_bgcolor="LightSteelBlue",
    )
    fig.update_xaxes(title_text="Date et heure")
    fig.update_yaxes(title_text=variable_label)

    return fig

def create_table(df: pd.DataFrame, datetime_label: str, variables_dic: dict[str, str]):
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=[datetime_label] + list(variables_dic.keys()),
                    font=dict(size=14),
                    line_color='darkslategray',
                    fill_color='paleturquoise',
                    align="left"
                ),
                cells=dict(
                    values=[df[var].tolist() for var in ["dt"] + list(variables_dic.values())],
                    line_color='darkslategray',
                    fill_color='lavender',
                    align="left"
                )
            )
        ]
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig
