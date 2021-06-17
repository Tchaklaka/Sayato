# coding: utf-8

import dash


# Serveur
app = dash.Dash(
    __name__,
    assets_folder="../assets",
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
