# Integración del Modelo de Predicción Climática

## 📦 Archivos Integrados

### 1. Modelo ML
- **Ubicación**: `ml/weather_model.pkl`
- **Tipo**: XGBoost Gradient Boosting (300 árboles)
- **Features**: 15 características avanzadas
- **Entrenado con**: NASA MERRA-2 (45 días de datos)
- **Métricas**: R² = 1.0000, MAE = 0.00°C

### 2. Código del Predictor
- **Ubicación**: `models/weather_predictor.py`
- **Clase**: `ImprovedWeatherPredictor`
- **Funcionalidad**: 
  - Carga el modelo entrenado
  - Predice temperatura y precipitación
  - Maneja datos faltantes con simulación estacional

### 3. API Flask
- **Archivo**: `routes/climate.py`
- **Endpoint**: `POST /api/climate/predict`
- **Entrada**:
  ```json
  {
    "lat": -6.7714,
    "lon": -79.8405,
    "fecha_inicio": "2025-10-06",
    "fecha_fin": "2025-10-12"
  }
  ```
- **Salida**:
  ```json
  {
    "success": true,
    "data": {
      "ubicacion": {"lat": -6.7714, "lon": -79.8405},
      "predicciones": [
        {
          "fecha": "2025-10-06",
          "dia_semana": "Monday",
          "temperatura": {
            "valor": 25.9,
            "min": 23.9,
            "max": 28.9,
            "unidad": "°C"
          },
          "precipitacion": {
            "lloverá": false,
            "probabilidad": 7.6,
            "confianza": "Alta"
          }
        }
      ],
      "modelo": "XGBoost Gradient Boosting",
      "fuente_datos": "NASA MERRA-2"
    }
  }
  ```

### 4. Interfaz Web
- **Archivo**: `views/modalPredictorClimatico.html`
- **Funcionalidad**:
  - Formulario para seleccionar ubicación y fechas
  - Llamada AJAX a la API de predicción
  - Visualización con Chart.js (gráfico de temperatura)
  - Íconos de clima por día (☀️ ⛅ 🌧️)
  - Recomendaciones inteligentes según actividad

## 🚀 Cómo Usar

### 1. Verificar que el modelo está cargado

```python
# Al iniciar la app, deberías ver en consola:
✅ Modelo de clima cargado exitosamente
```

Si ves:
```python
⚠️ Modelo no encontrado, usando predicción estacional
```

Significa que el modelo no está entrenado y usará **datos simulados**.

### 2. Probar la API manualmente

```bash
# Con curl o Postman
curl -X POST http://localhost:3307/api/climate/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lat": -6.7714,
    "lon": -79.8405,
    "fecha_inicio": "2025-10-06",
    "fecha_fin": "2025-10-12"
  }'
```

### 3. Usar desde la interfaz web

1. **Abrir la aplicación**: http://localhost:3307
2. **Seleccionar punto en el mapa** (coordenadas se guardan automáticamente)
3. **Abrir modal del predictor climático**
4. **Rellenar**:
   - Ubicación (se llena automáticamente)
   - Fecha de inicio
   - Fecha de fin
   - Seleccionar actividad
5. **Click en "Analiza las condiciones climáticas"**
6. **Ver resultados**:
   - Gráfico de temperatura (Chart.js)
   - Íconos del clima por día
   - Recomendación personalizada

## 📊 Datos Simulados vs Reales

### Modelo Entrenado (Datos Reales)
- ✅ Usa `weather_model.pkl`
- ✅ Predicciones basadas en XGBoost
- ✅ 15 features avanzadas
- ✅ Entrenado con NASA MERRA-2
- Consola muestra: `"nota": "Predicción basada en modelo entrenado"`

### Modelo NO Entrenado (Datos Simulados)
- ⚠️ No encuentra `weather_model.pkl`
- ⚠️ Usa fórmulas estacionales simples
- ⚠️ Random con seed para consistencia
- Consola muestra: `"nota": "⚠️ DATOS SIMULADOS - Modelo no entrenado"`
- Web muestra: **(⚠️ Datos Simulados)** en el título

## 🔍 Detección de Datos Simulados

En la **consola del navegador** (F12):

```javascript
// Datos reales
✅ Predicción recibida: {modelo: "XGBoost Gradient Boosting", ...}

// Datos simulados
⚠️ DATOS SIMULADOS: ⚠️ DATOS SIMULADOS - Para datos reales entrena el modelo
```

En la **consola del servidor Flask**:

```python
# Datos reales
🔮 Prediciendo clima para (-6.7714, -79.8405) desde 2025-10-06 hasta 2025-10-12
✅ 7 predicciones generadas

# Datos simulados
⚠️ SIMULANDO datos para (-6.7714, -79.8405)
⚠️ 7 predicciones SIMULADAS generadas
```

## 🎯 Recomendaciones Inteligentes

La interfaz analiza automáticamente las predicciones y genera recomendaciones:

### Condiciones Favorables (✅ Verde)
- Probabilidad de lluvia < 40%
- Menos de 2 días con lluvia
- Mensaje: "Condiciones favorables para [actividad]"

### Precaución (⚠️ Amarillo)
- Probabilidad de lluvia 40-70%
- 2-3 días con lluvia
- Mensaje: "Precaución, llevar equipo para lluvia"

### Desfavorable (❌ Rojo)
- Probabilidad de lluvia > 70%
- Más de 3 días con lluvia
- Mensaje: "Condiciones desfavorables, considerar reprogramar"

## 🛠️ Troubleshooting

### Error: "Modelo no encontrado"
**Solución**: El modelo `weather_model.pkl` no está en `ml/`. La app funcionará con datos simulados.

Para usar datos reales:
```bash
# Entrenar modelo
cd d:\DD
python weather_ml_pro\train_light.py

# Copiar modelo
Copy-Item "weather_ml_pro\models\improved_light_chiclayo.pkl" -Destination "Prensentable\TeamRocketHackaton\ml\weather_model.pkl"
```

### Error: "Cannot import ImprovedWeatherPredictor"
**Solución**: Verificar que `models/weather_predictor.py` existe.

### Error: "Chart is not defined"
**Solución**: Chart.js no se cargó. El modal incluye el CDN automáticamente.

### Error: "No se recibieron datos"
**Solución**: Verificar que las coordenadas se guardaron. Debe verse en consola:
```
📍 Coordenadas guardadas: -6.7714, -79.8405
```

## 📈 Arquitectura

```
┌─────────────────────────────────────┐
│   Interfaz Web (modalPredictor)    │
│   - Formulario ubicación/fechas     │
│   - Chart.js para gráficos          │
└──────────────┬──────────────────────┘
               │ AJAX POST
               ▼
┌─────────────────────────────────────┐
│   Flask API (/api/climate/predict)  │
│   - Valida datos                    │
│   - Llama al predictor              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Predictor (models/weather_pred..  │
│   - Carga modelo ML                 │
│   - Genera features                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Modelo ML (ml/weather_model.pkl)  │
│   - XGBoost 300 árboles             │
│   - 15 features avanzadas           │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Resultado JSON                    │
│   - Predicciones 7 días             │
│   - Temperatura + Precipitación     │
└─────────────────────────────────────┘
```

## 🎨 Visualización

### Gráfico de Temperatura
- **Librería**: Chart.js 4.4.0
- **Tipo**: Línea con 3 series (mín, promedio, máx)
- **Colores**:
  - Máxima: 🔴 Rojo (#ff6b6b)
  - Promedio: 💙 Azul (#4ecdc4)
  - Mínima: 🔵 Azul claro (#45b7d1)

### Íconos del Clima
- ☀️ **Despejado**: Probabilidad lluvia < 30%
- ⛅ **Parcialmente nublado**: Probabilidad 30-50%
- 🌧️ **Lluvia**: Probabilidad > 50%

## 📝 Notas Importantes

1. **Prototipo**: Este es un prototipo para hackathon con datos limitados (45 días)
2. **Producción**: Para producción real, entrenar con años de datos
3. **Alcance**: Predicción hasta 30 días (óptimo: 7-14 días)
4. **Regiones**: Entrenado para Chiclayo, Perú. Otras ubicaciones usan extrapolación
5. **Simulación**: Si no hay modelo, simula datos consistentes basados en estacionalidad

## 🚀 Mejoras Futuras

- [ ] Entrenar con más días de historia (180+)
- [ ] Incluir más variables (viento, presión, nubosidad)
- [ ] Caché de predicciones en base de datos
- [ ] Exportar a PDF las recomendaciones
- [ ] Notificaciones de alerta por clima adverso
- [ ] Integración con otras fuentes de datos (OpenWeather, etc.)

---

**Desarrollado para Team Rocket Hackathon** 🚀
**Modelo ML**: XGBoost + NASA MERRA-2
**Fecha**: Octubre 2025
