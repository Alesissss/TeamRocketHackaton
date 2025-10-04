
# nldas_predictor.py
# ------------------
# Public functions:
#   - predict_rain_prob(lat, lon, when_iso, horizon=6, model_path="nldas_rf.joblib", cols_path="nldas_features.txt")
#   - predict_rain_prob_range(lat, lon, start_iso, end_iso, freq="1H", horizon=6, ...)
#
# Requirements:
#   pip install pandas numpy scikit-learn requests joblib

import io
import urllib.parse as urlp
from typing import Dict, List
import numpy as np
import pandas as pd
import requests
from joblib import load

DATA_RODS_URL = "https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi"

VARIABLES = {
    "Rainf": "NLDAS2:NLDAS_FORA0125_H_v2.0:Rainf",
    "Tair":  "NLDAS2:NLDAS_FORA0125_H_v2.0:Tair",
    "Qair":  "NLDAS2:NLDAS_FORA0125_H_v2.0:Qair",
    "SoilM_0_100cm": "NLDAS2:NLDAS_NOAH0125_H_v2.0:SoilM_0_100cm",
    "Qh":    "NLDAS2:NLDAS_NOAH0125_H_v2.0:Qh",
    "Qg":    "NLDAS2:NLDAS_NOAH0125_H_v2.0:Qg",
    "Evap":  "NLDAS2:NLDAS_NOAH0125_H_v2.0:Evap",
}

def _get_time_series(start_date: str, end_date: str, latitude: float, longitude: float, variable: str, attempts: int = 3) -> str:
    params = {
        "variable": variable,
        "type": "asc2",
        "location": f"GEOM:POINT({longitude}, {latitude})",
        "startDate": start_date,
        "endDate": end_date,
    }
    full_url = DATA_RODS_URL + "?" + "&".join([f"{k}={urlp.quote(v)}" for k, v in params.items()])
    last = None
    for _ in range(attempts):
        r = requests.get(full_url, timeout=60)
        if r.status_code == 200:
            return r.text
        last = r
    raise RuntimeError(f"Data Rods error ({last.status_code}) for {variable}: {last.text[:200]}")

def _parse_time_series(ts_str: str) -> pd.DataFrame:
    df = pd.read_table(io.StringIO(ts_str), sep="\t", names=["time", "data"], header=10)
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df = df.dropna(subset=["time"]).set_index("time").sort_index()
    df["data"] = pd.to_numeric(df["data"], errors="coerce")
    return df

def _fetch_window(lat: float, lon: float, start_iso: str, end_iso: str) -> pd.DataFrame:
    frames = []
    for name, varid in VARIABLES.items():
        raw = _get_time_series(start_iso, end_iso, lat, lon, varid)
        df = _parse_time_series(raw).rename(columns={"data": name})
        frames.append(df)
    df_all = pd.concat(frames, axis=1).sort_index()
    df_all = df_all.resample("1H").mean().ffill(limit=2)
    return df_all

def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    idx = out.index.tz_convert("UTC")
    hour = idx.hour.to_numpy()
    doy = idx.dayofyear.to_numpy()
    out["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    out["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    out["doy_sin"] = np.sin(2 * np.pi * doy / 366.0)
    out["doy_cos"] = np.cos(2 * np.pi * doy / 366.0)
    return out

def _add_lags(df: pd.DataFrame, cols: List[str], lags=(1,3,6,24)) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        for L in lags:
            out[f"{c}_lag{L}h"] = out[c].shift(L)
    return out

def _build_features(df_hist: pd.DataFrame, horizon_h: int = 6) -> pd.DataFrame:
    feat = _add_time_features(df_hist)
    feat = _add_lags(feat, list(VARIABLES.keys()), lags=(1,3,6,24))
    for col in ["Tair","Qair","Evap","Qh","Qg"]:
        if col in feat.columns:
            feat[f"{col}_roll6h"] = feat[col].rolling(6, min_periods=3).mean()
    # Build and keep the last row only (for inference at end of window)
    X = feat.dropna().iloc[[-1]]
    return X

def _align_columns(X: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    for c in feature_cols:
        if c not in X.columns:
            X[c] = np.nan
    X = X[feature_cols].fillna(method="ffill").fillna(0.0)
    return X

def _load_artifacts(model_path: str, cols_path: str):
    pipe = load(model_path)
    with open(cols_path, "r", encoding="utf-8") as f:
        cols = [line.strip() for line in f if line.strip()]
    return pipe, cols

def predict_rain_prob(lat: float, lon: float, when_iso: str, horizon: int = 6,
                      model_path: str = "nldas_rf.joblib", cols_path: str = "nldas_features.txt") -> Dict[str, float]:
    """
    One-shot prediction: given lat/lon and a UTC datetime string (YYYY-MM-DDTHH),
    fetches the last 48h of NLDAS data, builds features, loads the model and
    returns the probability of rain in the next `horizon` hours.
    """
    # Build a 48h window ending at 'when'
    when = pd.to_datetime(when_iso, utc=True)
    start_iso = (when - pd.Timedelta(hours=48)).strftime("%Y-%m-%dT%H")
    end_iso = when.strftime("%Y-%m-%dT%H")

    df_hist = _fetch_window(lat, lon, start_iso, end_iso)
    X = _build_features(df_hist, horizon_h=horizon)

    pipe, feat_cols = _load_artifacts(model_path, cols_path)
    X = _align_columns(X, feat_cols)

    proba = float(pipe.predict_proba(X)[:, 1][0])
    return {
        "lat": float(lat),
        "lon": float(lon),
        "when_utc": when_iso,
        "horizon_hours": int(horizon),
        "prob_rain_next_h": proba,
        "will_rain": bool(proba >= 0.5)
    }

def predict_rain_prob_range(lat: float, lon: float, start_iso: str, end_iso: str, freq: str = "1H",
                            horizon: int = 6, model_path: str = "nldas_rf.joblib", cols_path: str = "nldas_features.txt"
                           ) -> pd.DataFrame:
    """
    Batch predictions for a time range. For each timestamp in [start, end] with step `freq`,
    compute P(rain in next horizon h). Returns a DataFrame indexed by time.
    """
    times = pd.date_range(pd.to_datetime(start_iso, utc=True), pd.to_datetime(end_iso, utc=True), freq=freq)
    rows = []
    for t in times:
        res = predict_rain_prob(lat, lon, t.strftime("%Y-%m-%dT%H"), horizon=horizon, model_path=model_path, cols_path=cols_path)
        rows.append((t, res["prob_rain_next_h"], res["will_rain"]))
    out = pd.DataFrame(rows, columns=["time", "prob_rain_next_h", "will_rain"]).set_index("time")
    return out
