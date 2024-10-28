"""Dự đoán khách hàng rời bỏ (churn).

Định nghĩa nhãn: khách được coi là ĐÃ rời bỏ nếu không có giao dịch nào
trong `churn_window_days` ngày cuối tính tới ngày snapshot (mặc định 120).

Đặc trưng cho mô hình KHÔNG gồm recency thô (vì nhãn suy trực tiếp từ
recency nên đưa vào sẽ thành rò rỉ dữ liệu — data leakage). Thay vào đó
dùng recency_ratio = recency / khoảng cách mua trung bình của chính khách
đó, cùng frequency, monetary, AOV, tenure, độ đa dạng sản phẩm, tỉ lệ
đơn có khuyến mãi.

Danh sách "nguy cơ cao" = khách CHƯA rời bỏ theo nhãn nhưng mô hình cho
xác suất rời bỏ cao — đây mới là nhóm cần chăm sóc giữ chân.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

FEATURES = ["frequency", "monetary", "aov", "tenure_days", "unique_products",
            "avg_gap_days", "recency_ratio", "promo_share"]


def build_customer_features(df: pd.DataFrame,
                            snapshot: pd.Timestamp | None = None) -> pd.DataFrame:
    if snapshot is None:
        snapshot = df["invoice_date"].max() + pd.Timedelta(days=1)
    inv = (df.groupby(["customer_id", "invoice_id"])
             .agg(date=("invoice_date", "max"), total=("revenue", "sum"),
                  promo=("discount_pct", lambda s: (s > 0).any()))
             .reset_index())
    rows = []
    for cid, g in inv.groupby("customer_id"):
        dates = sorted(g["date"])
        gaps = np.diff([d.value for d in dates]) / 8.64e13 if len(dates) > 1 else np.array([])
        avg_gap = float(gaps.mean()) if len(gaps) else 365.0
        recency = (snapshot - dates[-1]).days
        rows.append({
            "customer_id": cid,
            "recency": recency,
            "frequency": len(g),
            "monetary": float(g["total"].sum()),
            "aov": float(g["total"].mean()),
            "tenure_days": max((dates[-1] - dates[0]).days, 1),
            "unique_products": int(df.loc[df["customer_id"] == cid, "product_id"].nunique()),
            "avg_gap_days": avg_gap,
            "recency_ratio": recency / avg_gap if avg_gap > 0 else float(recency),
            "promo_share": float(g["promo"].mean()),
            "last_purchase": dates[-1],
        })
    return pd.DataFrame(rows)


def label_churn(feat: pd.DataFrame, churn_window_days: int = 120) -> pd.DataFrame:
    out = feat.copy()
    out["churned"] = (out["recency"] > churn_window_days).astype(int)
    return out


def train_churn_models(feat: pd.DataFrame, random_state: int = 42) -> dict:
    """Huấn luyện Logistic Regression + Random Forest, trả metrics thật
    trên tập test (stratified split 75/25) và xác suất cho mọi khách."""
    X = feat[FEATURES].fillna(0)
    y = feat["churned"]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=random_state, stratify=y)
    scaler = StandardScaler().fit(X_tr)
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, random_state=random_state, n_jobs=-1),
    }
    results = {}
    proba = {}
    for name, model in models.items():
        Xtr = scaler.transform(X_tr) if name == "Logistic Regression" else X_tr
        Xte = scaler.transform(X_te) if name == "Logistic Regression" else X_te
        model.fit(Xtr, y_tr)
        pred = model.predict(Xte)
        p = model.predict_proba(Xte)[:, 1]
        results[name] = {
            "accuracy": float(accuracy_score(y_te, pred)),
            "roc_auc": float(roc_auc_score(y_te, p)),
        }
        Xall = scaler.transform(X) if name == "Logistic Regression" else X
        proba[name] = model.predict_proba(Xall)[:, 1]
    best = max(results, key=lambda k: results[k]["roc_auc"])
    out = feat.copy()
    out["churn_probability"] = proba[best]
    return {"metrics": results, "best_model": best, "features": out,
            "churn_rate_pct": float(y.mean() * 100),
            "n_churned": int(y.sum()), "n_customers": int(len(y))}


def high_risk_customers(features: pd.DataFrame,
                        prob_threshold: float = 0.5) -> pd.DataFrame:
    """Khách chưa rời bỏ (nhãn 0) nhưng xác suất rời bỏ >= ngưỡng."""
    risk = features[(features["churned"] == 0)
                    & (features["churn_probability"] >= prob_threshold)]
    cols = ["customer_id", "churn_probability", "recency", "frequency",
            "monetary", "last_purchase"]
    return (risk.sort_values("churn_probability", ascending=False)[cols]
            .reset_index(drop=True))
