# coding: utf-8

import os

import pandas as pd


root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Ressource : liste des capitales mondiales avec leurs coordonnées
capitals = pd.read_csv(os.path.join(root_dir, "data", "concap.csv")).dropna().reset_index(drop=True)
