
"""
NLDAS2 ML — Train & Predict with scikit-learn
---------------------------------------------
Predicts probability of rain in the next 6 hours (binary classification)
from NLDAS2 surface variables fetched via NASA Data Rods.

Usage:
  1) Install deps:
       pip install -r requirements.txt
     or:
       pip install pandas numpy scikit-learn requests joblib matplotlib

  2) Train (downloads data for LAT/LON and saves model to disk):
       python train_nldas_ml.py --lat 38.89 --lon -88.18 --start "2022-07-01T00" --end "2025-09-01T00"

  3) Predict for a specific datetime (UTC) using the trained model.
     It will fetch the last 24 hours up to `when`, build features and predict rain in next 6h:
       python train_nldas_ml.py --predict --lat 38.89 --lon -88.18 --when "2025-09-01T00"

Notes:
  - Horizon is configurable (default 6 hours). Adjust via --horizon 3|6|12|24
  - For robust operation in a web app, keep the trained .joblib on disk and
    only fetch the *recent* 24h window at request time to build features.
"""

import argparse
import io
import math
import sys
import urllib.parse as urlp
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests
from joblib import dump, load
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

def lon_to_0360(lon):
    # lon en [-180,180] → [0,360)
    return (lon + 360.0) % 360.0

def lon_to_180(lon):
    # lon en [0,360) → [-180,180]
    return ((lon + 180.0) % 360.0) - 180.0

DATA_RODS_URL = "https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi"

# Variables we will use
VARIABLES = {
    # dataset:variable
    "Rainf": "NLDAS2:NLDAS_FORA0125_H_v2.0:Rainf",          # precipitation [kg m-2]
    "Tair":  "NLDAS2:NLDAS_FORA0125_H_v2.0:Tair",           # 2m air temperature [K]
    "Qair":  "NLDAS2:NLDAS_FORA0125_H_v2.0:Qair",           # 2m specific humidity [kg/kg]
    "SoilM_0_100cm": "NLDAS2:NLDAS_NOAH0125_H_v2.0:SoilM_0_100cm", # soil moisture [kg m-2]
    "Qh":    "NLDAS2:NLDAS_NOAH0125_H_v2.0:Qh",             # sensible heat flux [W m-2]
    "Qg":    "NLDAS2:NLDAS_NOAH0125_H_v2.0:Qg",             # ground heat flux [W m-2]
    "Evap":  "NLDAS2:NLDAS_NOAH0125_H_v2.0:Evap",           # total evapotranspiration [kg m-2]
}

@dataclass
class FetchConfig:
    start_date: str
    end_date: str
    lat: float
    lon: float

def get_time_series(start_date: str, end_date: str, latitude: float, longitude: float, variable: str, attempts: int = 3) -> str:
    """Call NASA Data Rods and return the raw ASCII time-series response."""
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

def parse_time_series(ts_str: str) -> pd.DataFrame:
    """Parse Data Rods ASCII into a DataFrame with columns ['time','data'] and datetime index."""
    # Header: first 10 lines contain metadata. Then TSV with two columns
    df = pd.read_table(io.StringIO(ts_str), sep="\t", names=["time", "data"], header=10)
    # 'time' is already ISO; pandas can parse it directly
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df = df.dropna(subset=["time"]).set_index("time").sort_index()
    # Ensure numeric
    df["data"] = pd.to_numeric(df["data"], errors="coerce")
    return df

def fetch_all(cfg: FetchConfig) -> pd.DataFrame:
    """Fetch all VARIABLES for the given window and return a merged hourly dataframe."""
    frames = []
    for name, varid in VARIABLES.items():
        raw = get_time_series(cfg.start_date, cfg.end_date, cfg.lat, cfg.lon, varid)
        df = parse_time_series(raw).rename(columns={"data": name})
        frames.append(df)
    df_all = pd.concat(frames, axis=1).sort_index()
    # Align to hourly and forward-fill small gaps
    df_all = df_all.resample("1H").mean()
    df_all = df_all.ffill(limit=2)
    return df_all

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add cyclical time features (hour of day, day of year)."""
    out = df.copy()
    idx = out.index.tz_convert("UTC")
    hour = idx.hour.to_numpy()
    doy = idx.dayofyear.to_numpy()
    out["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    out["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    out["doy_sin"] = np.sin(2 * np.pi * doy / 366.0)
    out["doy_cos"] = np.cos(2 * np.pi * doy / 366.0)
    return out

def add_lag_features(df: pd.DataFrame, cols, lags=(1, 3, 6, 24)) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        for L in lags:
            out[f"{c}_lag{L}h"] = out[c].shift(L)
    return out

def build_dataset(df_hourly: pd.DataFrame, horizon_h: int = 6, rain_threshold: float = 0.1) -> pd.DataFrame:
    """
    Build modeling table:
      - Features: original series + lags + rolling means + time cycles
      - Target: Rain in next `horizon_h` hours (>= rain_threshold)
    """
    base = df_hourly.copy()
    # Feature engineering
    feat = add_time_features(base)
    feat = add_lag_features(feat, cols=list(VARIABLES.keys()), lags=(1, 3, 6, 24))
    # Rolling means to reduce noise (on key drivers)
    for col in ["Tair", "Qair", "Evap", "Qh", "Qg"]:
        if col in feat.columns:
            feat[f"{col}_roll6h"] = feat[col].rolling(6, min_periods=3).mean()
    # Target: rain in [t+1 .. t+horizon] (any rainfall above threshold)
    future = base["Rainf"].shift(-horizon_h)
    y = (future >= rain_threshold).astype(int).rename("will_rain")
    Xy = pd.concat([feat, y], axis=1).dropna()
    return Xy

def time_train_test_split(df: pd.DataFrame, test_start: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by absolute timestamp (no leakage)."""
    ts = pd.to_datetime(test_start, utc=True)
    train = df[df.index < ts]
    test = df[df.index >= ts]
    return train, test

def train_model(train_df: pd.DataFrame) -> Pipeline:
    """Train a RandomForest classifier in a scikit-learn Pipeline with scaling for safety."""
    y = train_df["will_rain"].to_numpy()
    X = train_df.drop(columns=["will_rain"])
    # We will scale only continuous features (Safe with trees; harmless)
    numeric_cols = list(X.columns)
    pre = ColumnTransformer([("num", StandardScaler(with_mean=False), numeric_cols)], remainder="drop")
    clf = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_split=4,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced_subsample",
    )
    pipe = Pipeline([("pre", pre), ("clf", clf)])
    pipe.fit(X, y)
    return pipe

def evaluate(pipe: Pipeline, test_df: pd.DataFrame) -> dict:
    y_true = test_df["will_rain"].to_numpy()
    X_test = test_df.drop(columns=["will_rain"])
    proba = pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "confusion_matrix": confusion_matrix(y_true, pred).tolist(),
        "report": classification_report(y_true, pred, digits=3),
    }
    return metrics

def save_artifacts(pipe: Pipeline, feature_cols: list[str], path_model="nldas_rf.joblib", path_cols="nldas_features.txt"):
    dump(pipe, path_model)
    with open(path_cols, "w", encoding="utf-8") as f:
        for c in feature_cols:
            f.write(c + "\n")

def load_artifacts(path_model="nldas_rf.joblib", path_cols="nldas_features.txt"):
    pipe = load(path_model)
    with open(path_cols, "r", encoding="utf-8") as f:
        cols = [line.strip() for line in f if line.strip()]
    return pipe, cols

def build_features_for_inference(lat: float, lon: float, when_iso: str, horizon_h: int = 6) -> pd.DataFrame:
    """
    Fetch the last 24h up to `when` (inclusive) and build ONE-row feature vector
    to predict rain in the next `horizon_h` hours.
    """
    when = pd.to_datetime(when_iso, utc=True)
    start = (when - pd.Timedelta(hours=48)).strftime("%Y-%m-%dT%H")
    end = when.strftime("%Y-%m-%dT%H")
    df_hist = fetch_all(FetchConfig(start, end, lat, lon))
    # Build a dataset in the same way, but we only need the last available row's features
    Xy = build_dataset(df_hist, horizon_h=horizon_h)
    # Keep the last row of features (target is unknown for future; drop it if present)
    X_one = Xy.drop(columns=["will_rain"]).iloc[[-1]]
    return X_one

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True, help="Latitude (deg)")
    ap.add_argument("--lon", type=float, required=True, help="Longitude (deg, West negative)")
    ap.add_argument("--start", type=str, default="2022-07-01T00", help="Start date (UTC, YYYY-MM-DDTHH)")
    ap.add_argument("--end", type=str, default="2025-09-01T00", help="End date (UTC, YYYY-MM-DDTHH)")
    ap.add_argument("--test_start", type=str, default="2025-01-01T00", help="Test set start (UTC)")
    ap.add_argument("--horizon", type=int, default=6, help="Prediction horizon in hours")
    ap.add_argument("--rain_threshold", type=float, default=0.1, help="Rain threshold (kg m-2) to define positive")
    ap.add_argument("--model_path", type=str, default="nldas_rf.joblib")
    ap.add_argument("--cols_path", type=str, default="nldas_features.txt")
    ap.add_argument("--predict", action="store_true", help="Run single prediction instead of training")
    ap.add_argument("--when", type=str, default=None, help="Datetime (UTC) for prediction, e.g., 2025-09-01T00")
    args = ap.parse_args()

    if args.predict:
        # Inference path: load artifacts and predict for given time
        if args.when is None:
            print("--predict requires --when ISO datetime", file=sys.stderr)
            sys.exit(2)
        pipe, feat_cols = load_artifacts(args.model_path, args.cols_path)
        X = build_features_for_inference(args.lat, args.lon, args.when, args.horizon)

        # Align columns (add missing, drop extra), keeping order used in training
        for c in feat_cols:
            if c not in X.columns:
                X[c] = np.nan
        X = X[feat_cols].fillna(method="ffill").fillna(0.0)

        proba = pipe.predict_proba(X)[:, 1][0]
        label = int(proba >= 0.5)
        print(f"Prediction for {args.when} at ({args.lat}, {args.lon}): P(rain next {args.horizon}h) = {proba:.3f}  =>  will_rain={label}")
        return

    # Train path: fetch full history, build dataset, time split, train, eval, save
    cfg = FetchConfig(args.start, args.end, args.lat, args.lon)
    print("Fetching NLDAS2 variables...")
    df_all = fetch_all(cfg)
    print("Building modeling dataset...")
    Xy = build_dataset(df_all, horizon_h=args.horizon, rain_threshold=args.rain_threshold)

    print(f"Rows after feature engineering: {len(Xy):,}")
    train_df, test_df = time_train_test_split(Xy, test_start=args.test_start)
    print(f"Train rows: {len(train_df):,} | Test rows: {len(test_df):,}")

    print("Training RandomForest classifier...")
    pipe = train_model(train_df)

    print("Evaluating on holdout...")
    metrics = evaluate(pipe, test_df)
    print(f"ROC AUC: {metrics['roc_auc']:.3f}")
    print("Confusion matrix [[TN, FP], [FN, TP]]:", metrics["confusion_matrix"])
    print(metrics["report"])

    # Save artifacts
    feat_cols = list(train_df.drop(columns=["will_rain"]).columns)
    save_artifacts(pipe, feat_cols, path_model=args.model_path, path_cols=args.cols_path)
    print(f"Saved model -> {args.model_path}")
    print(f"Saved feature list -> {args.cols_path}")

if __name__ == "__main__":
    main()
