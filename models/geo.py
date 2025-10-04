import requests

class API:
    def api_lat_long(self, lat, long):

        #se usara la api de Reverse Geocoding para obtener la direccion a partir de las coordenadas
        # https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=-34.44076&lon=-58.70521

        datos = []

        response = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={long}")
        if response.status_code == 200:
            data = response.json()

            # Extraer la información relevante
            address = data.get("address", {})
            departamento = address.get("state", "") or ""
            provincia = address.get("region", "") or ""
            distrito = address.get("village", "") or address.get("town", "") or address.get("suburb", "") or address.get("city", "") or address.get("hamlet", "") or ""
            direccionCompleta = data.get("display_name", "") or "Dirección no disponible"
            country_code = address.get("country_code", "") or ""

            datos.append({
                "departamento": departamento,
                "provincia": provincia,
                "distrito": distrito,
                "direccionCompleta": direccionCompleta,
                "country_code": country_code
            })

            return datos
        else:
            return f"Latitud: {lat}, Longitud: {long}, Error: No se pudo obtener la dirección"

    



    


