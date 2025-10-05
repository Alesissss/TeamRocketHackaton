import os
from flask import Flask, render_template, request, redirect, flash, jsonify, session, url_for, abort, send_from_directory
from flask_babel import Babel, _, get_locale
from utils.translations import get_translation
from routes.home import bp_home
from routes.geo import bp_geo
from routes.climate import bp_climate

app = Flask(__name__, template_folder="views", static_folder="static")

# Clave secreta para sesiones (necesaria para usar `session`)
app.secret_key = os.urandom(24)  # O usa una clave fija: app.secret_key = "mi_clave_secreta"

# Configuración de Babel
app.config['LANGUAGES'] = {
    'en': 'English',
    'es': 'Español'
}
app.config['BABEL_DEFAULT_LOCALE'] = 'es'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'

babel = Babel()
babel.init_app(app)

def get_locale():
    # 1. Si está en la URL
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    # 2. Si está en la sesión
    if 'lang' in session and session['lang'] in app.config['LANGUAGES']:
        return session['lang']
    # 3. Por defecto, usar el español
    return 'es'

# Registrar la función locale selector
babel.locale_selector_func = get_locale

# Hacer funciones de Babel disponibles en templates
@app.context_processor
def inject_conf_vars():
    def translate(text):
        current_lang = session.get('lang', 'es')
        return get_translation(text, current_lang)
    
    return dict(
        _=translate,
        get_locale=get_locale
    )

app.register_blueprint(bp_home)
app.register_blueprint(bp_geo)
app.register_blueprint(bp_climate)


if __name__ == "__main__":
    app.run(debug=True, port=3307)