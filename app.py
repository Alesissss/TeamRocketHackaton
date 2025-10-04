import os
from flask import Flask, render_template, request, redirect, flash, jsonify, session, url_for, abort, send_from_directory
from routes.home import bp_home
from routes.geo import bp_geo
from routes.climate import bp_climate

app = Flask(__name__, template_folder="views", static_folder="static")

# Clave secreta para sesiones (necesaria para usar `session`)
app.secret_key = os.urandom(24)  # O usa una clave fija: app.secret_key = "mi_clave_secreta"

app.register_blueprint(bp_home)
app.register_blueprint(bp_geo)
app.register_blueprint(bp_climate)


if __name__ == "__main__":
    app.run(debug=True, port=3307)