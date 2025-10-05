from flask import Blueprint, request, jsonify
from models.geo import API

bp_geo = Blueprint('geo', __name__)

api = API()

@bp_geo.route('/geocode', methods=['GET'])
def geocode():
    lat = request.args.get('lat')
    long = request.args.get('long')

    if lat is None or long is None:
        return jsonify({"error": "Parameters are missing 'lat' or 'long'"}), 400
    
    response = api.api_lat_long(lat, long)

    if response:
        return jsonify(response), 200

    return jsonify({"error": "Geocoding failed"}), 500

