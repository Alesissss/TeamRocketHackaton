from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import sys
import os

# Añadir ruta de models al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))

# Importar predictor
try:
    from models.weather_predictor import ImprovedWeatherPredictor
    PREDICTOR_AVAILABLE = True
except Exception as e:
    print(f"⚠️ No se pudo importar predictor: {e}")
    PREDICTOR_AVAILABLE = False

bp_climate = Blueprint('climate', __name__)

# Cargar modelo al iniciar
predictor = None
if PREDICTOR_AVAILABLE:
    try:
        predictor = ImprovedWeatherPredictor()
        model_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'weather_model.pkl')
        if os.path.exists(model_path):
            predictor.load(model_path)
            print("✅ Modelo de clima cargado exitosamente")
        else:
            print("⚠️ Modelo no encontrado, usando predicción estacional")
    except Exception as e:
        print(f"❌ Error al cargar modelo: {e}")
        predictor = None


@bp_climate.route('/api/climate/predict', methods=['POST'])
def predict_climate():
    """
    API para predicción climática
    Recibe: ubicacion (lat, lon), fecha_inicio, fecha_fin
    Devuelve: predicciones día a día
    """
    try:
        data = request.get_json()
        
        # Validar datos
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos"
            }), 400
        
        # Extraer coordenadas
        lat = data.get('lat') or data.get('latitude')
        lon = data.get('lon') or data.get('longitude')
        
        if lat is None or lon is None:
            return jsonify({
                "success": False,
                "error": "Se requieren coordenadas (lat, lon)"
            }), 400
        
        # Convertir a float
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Coordenadas inválidas"
            }), 400
        
        # Extraer fechas
        fecha_inicio_str = data.get('fecha_inicio')
        fecha_fin_str = data.get('fecha_fin')
        
        # Si no hay fechas, predecir próximos 7 días
        if not fecha_inicio_str:
            fecha_inicio = datetime.now()
        else:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Formato de fecha inválido (usar YYYY-MM-DD)"
                }), 400
        
        if not fecha_fin_str:
            fecha_fin = fecha_inicio + timedelta(days=7)
        else:
            try:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Formato de fecha fin inválido (usar YYYY-MM-DD)"
                }), 400
        
        # Calcular días a predecir
        dias_total = (fecha_fin - fecha_inicio).days + 1
        
        if dias_total > 30:
            return jsonify({
                "success": False,
                "error": "El rango máximo es 30 días"
            }), 400
        
        if dias_total < 1:
            return jsonify({
                "success": False,
                "error": "La fecha de fin debe ser posterior a la fecha de inicio"
            }), 400
        
        # Hacer predicción
        if predictor:
            print(f"🔮 Prediciendo clima para ({lat}, {lon}) desde {fecha_inicio.date()} hasta {fecha_fin.date()}")
            predicciones = []
            
            fecha_actual = fecha_inicio
            for i in range(dias_total):
                pred = predictor.predict_single_day(lon, lat, fecha_actual)
                predicciones.append(pred)
                fecha_actual += timedelta(days=1)
            
            print(f"✅ {len(predicciones)} predicciones generadas")
            
            return jsonify({
                "success": True,
                "data": {
                    "ubicacion": {
                        "lat": lat,
                        "lon": lon
                    },
                    "fecha_inicio": fecha_inicio.strftime('%Y-%m-%d'),
                    "fecha_fin": fecha_fin.strftime('%Y-%m-%d'),
                    "dias_total": dias_total,
                    "predicciones": predicciones,
                    "modelo": "XGBoost Gradient Boosting",
                    "fuente_datos": "NASA MERRA-2",
                    "nota": "Predicción basada en modelo entrenado" if os.path.exists(
                        os.path.join(os.path.dirname(__file__), '..', 'ml', 'weather_model.pkl')
                    ) else "⚠️ Predicción simulada - Modelo no entrenado"
                }
            })
        else:
            # Si no hay predictor, simular datos
            print(f"⚠️ SIMULANDO datos para ({lat}, {lon})")
            predicciones = []
            
            fecha_actual = fecha_inicio
            for i in range(dias_total):
                # Simulación simple basada en estacionalidad
                import numpy as np
                np.random.seed(fecha_actual.timetuple().tm_yday + fecha_actual.year)
                
                temp_base = 22.0 + 4.0 * np.sin(2 * np.pi * (fecha_actual.month - 8) / 12)
                temp = temp_base + np.random.normal(0, 1.5)
                
                lluvia_prob = 0.45 if fecha_actual.month in [12, 1, 2, 3] else 0.08
                lluvia_prob += np.random.uniform(-0.1, 0.2)
                lluvia_prob = np.clip(lluvia_prob, 0, 0.9) * 100
                
                pred = {
                    'fecha': fecha_actual.strftime('%Y-%m-%d'),
                    'dia_semana': fecha_actual.strftime('%A'),
                    'temperatura': {
                        'valor': round(temp, 1),
                        'min': round(temp - 2, 1),
                        'max': round(temp + 3, 1),
                        'unidad': '°C'
                    },
                    'precipitacion': {
                        'lloverá': lluvia_prob > 50,
                        'probabilidad': round(lluvia_prob, 1),
                        'confianza': 'Media'
                    },
                    'ubicacion': {'lat': lat, 'lon': lon}
                }
                predicciones.append(pred)
                fecha_actual += timedelta(days=1)
            
            print(f"⚠️ {len(predicciones)} predicciones SIMULADAS generadas")
            
            return jsonify({
                "success": True,
                "data": {
                    "ubicacion": {
                        "lat": lat,
                        "lon": lon
                    },
                    "fecha_inicio": fecha_inicio.strftime('%Y-%m-%d'),
                    "fecha_fin": fecha_fin.strftime('%Y-%m-%d'),
                    "dias_total": dias_total,
                    "predicciones": predicciones,
                    "modelo": "Simulación estacional",
                    "fuente_datos": "Simulado",
                    "nota": "⚠️ DATOS SIMULADOS - Para datos reales entrena el modelo con: python weather_ml_pro/train_light.py"
                }
            })
    
    except Exception as e:
        import traceback
        print(f"❌ Error en predicción: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp_climate.route('/test/climate')
def test_climate():
    """Endpoint de prueba"""
    return jsonify({
        "message": "API de predicción climática activa",
        "modelo_cargado": predictor is not None,
        "endpoints": {
            "/api/climate/predict": "POST - Predicción climática"
        },
        "ejemplo": {
            "method": "POST",
            "url": "/api/climate/predict",
            "body": {
                "lat": -6.7714,
                "lon": -79.8405,
                "fecha_inicio": "2025-10-06",
                "fecha_fin": "2025-10-12"
            }
        }
    })