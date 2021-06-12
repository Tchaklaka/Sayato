# coding: utf-8

from typing import Optional

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go


def generate_dropdown(options: dict[str, str], init_value: str, identifier: str, options_filter: Optional[list[str]]=None):
    if options_filter is None:
        options_filter = list(options.values())
    return dcc.Dropdown(
        options=[{'label': key, 'value': val} for key, val in options.items() if val in options_filter],
        value=init_value,
        clearable=False,
        searchable=False,
        id=identifier
    )

def generate_layout(layers: dict[str, str]={}, variables: dict[str, str]={}, init_layer: str="", init_variable: str="", variables_quanti: list[str]=[], init_map: go.Figure=go.Figure()):
    dropdown_layers = generate_dropdown(layers, init_layer, "layers-dropdown")
    dropdown_variables = generate_dropdown(variables, init_variable, "variables-prevision-dropdown", options_filter=variables_quanti)

    layout = html.Div([
        html.Div([
            html.Div([
            ], className="col-1"),

            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.H1("Bulletin météo de SAYATO")
                        ], className='col-9 bg-light'),
                        
                        html.Div([
                            html.Div([
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
                                                    dropdown_layers
                                                ], className='col-12')
                                            ], className='row')
                                        ], className='container-sm')
                                    ], className='col-12')
                                ], className='row')
                            ], className='container-sm')
                        ], className='col-3 bg-info')
                    ], className='row'),

                    html.Div([
                        dcc.Graph(
                            id='mapmonde',
                            figure=init_map,
                            className="col-12 aspect-ratio-box-inside"
                        )
                    ], className="row aspect-ratio-box bg-info"),

                    html.Div([
                        html.Div([
                            html.Div([
                                html.H2(html.I("", id="capitale-name"))
                            ], className="d-flex justify-content-center")
                        ], className="col-12")
                    ], className="row bg-secondary"),
                    
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.H2("Principaux indicateurs")
                                    ], className='col-12')
                                ], className='row'),

                                html.Div([
                                    dcc.Graph(
                                        id='indicateur',
                                        config={'displayModeBar': False, 'staticPlot': True},
                                        className="col-12 bg-light"
                                    )
                                ], className="row bg-light"),
                            ], className='container-sm bg-light')
                        ], className='col-12 bg-light')
                    ], className="row bg-light"),

                    html.Div([
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.H2("Graphique des prévisions sur 48h")
                                    ], className='col-9 bg-info'),
                                    
                                    html.Div([
                                        html.Div([
                                            html.Div([
                                                html.Div([
                                                    html.Div([
                                                        html.Div([
                                                            html.Br()
                                                        ], className='row'),

                                                        html.Div([
                                                            html.Div([
                                                                dropdown_variables
                                                            ], className='col-12')
                                                        ], className='row')
                                                    ], className='container-sm')
                                                ], className='col-12')
                                            ], className='row')
                                        ], className='container-sm')
                                    ], className='col-3 bg-info')
                                ], className='row'),

                                html.Div([
                                    dcc.Graph(
                                        id='graphe-serie',
                                        className="col-12"
                                    )
                                ], className="row bg-info")
                            ], className='container-sm bg-info')
                        ], className='col-12 bg-info')
                    ], className="row bg-info"),
                    
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.H2("Tableau des prévisions sur 48h")
                                    ], className='col-12')
                                ], className='row'),

                                html.Div([
                                    dcc.Graph(
                                        id='tab',
                                        config={'displayModeBar': False},
                                        className="col-12 aspect-ratio-box-inside bg-light"
                                    )
                                ], className="row aspect-ratio-box bg-light"),
                            ], className='container-sm bg-light')
                        ], className='col-12 bg-light')
                    ], className="row bg-light")
                ], className='container-fluid')
            ], className="col-10"),
            
            html.Div([
            ], className="col-1")
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
    ], className="container-fluid")

    return layout
