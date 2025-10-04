from flask import Blueprint, request, jsonify

bp_climate = Blueprint('climate', __name__)

@bp_climate.route('/test/climate')
def test_climate():
    return jsonify({"message": "aca va la api de los machin lernin"})