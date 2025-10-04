
# example_predict.py
# Minimal usage demo (requires a trained model on disk).

from nldas_predictor import predict_rain_prob, predict_rain_prob_range

if __name__ == "__main__":
    def lon_to_0360(lon):
        # lon en [-180,180] → [0,360)
        return (lon + 360.0) % 360.0

    def lon_to_180(lon):
        # lon en [0,360) → [-180,180]
        return ((lon + 180.0) % 360.0) - 180.0

    # Ejemplo:
    print(lon_to_0360(-58.4))  # 301.6
    print(lon_to_180(302.0))   # -58.0 (aprox)


    print("Single point prediction:")
    res = predict_rain_prob(lat=38.89, lon=lon_to_0360(-88.18), when_iso="2025-09-01T00", horizon=6,
                            model_path="nldas_rf.joblib", cols_path="nldas_features.txt")
    print(res)

    print("\nRange prediction:")
    dfp = predict_rain_prob_range(lat=38.89, lon=-88.18, start_iso="2025-08-31T00", end_iso="2025-09-01T00",
                                  freq="3H", horizon=6, model_path="nldas_rf.joblib", cols_path="nldas_features.txt")
    print(dfp.head())
