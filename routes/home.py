from flask import Blueprint, render_template, request, jsonify, send_from_directory, redirect, url_for, session

bp_home = Blueprint('home', __name__)

@bp_home.route('/')
def home():
    return redirect(url_for('home.index'))

@bp_home.route('/home')
def index():
    return render_template('welcome_page.html')

@bp_home.route('/menu')
def menu():
    return render_template('menu.html')

@bp_home.route('/modal-predictor')
def modal_predictor():
    # Renderiza solo el contenido del modal
    return render_template('modalPredictorClimatico.html')

@bp_home.route('/change_language/<language>')
def change_language(language):
    session['lang'] = language
    # Redirigir a la página de donde vino o al home
    return redirect(request.referrer or url_for('home.index'))

@bp_home.route('/uploads/<path:filename>')
def uploads(filename):
    return send_from_directory('uploads', filename)

@bp_home.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)