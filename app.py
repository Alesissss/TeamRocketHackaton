import os
from flask import Flask, render_template, request, redirect, flash, jsonify, session, url_for, abort, send_from_directory

app = Flask(__name__, template_folder="views", static_folder="static")

# Clave secreta para sesiones (necesaria para usar `session`)
app.secret_key = os.urandom(24)  # O usa una clave fija: app.secret_key = "mi_clave_secreta"



if __name__ == "__main__":
    app.run(debug=True, port=3307)