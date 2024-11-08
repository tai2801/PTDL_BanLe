"""Test các quy tắc phân tích cốt lõi bằng dữ liệu nhỏ biết trước kết quả."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analytics import (compute_kpi, compute_rfm, detect_revenue_anomalies,
                           monthly_revenue)
from src.basket import basket_pairs
from src.cleaning import SchemaError, clean_transactions, validate_schema
from src.churn import build_customer_features, label_churn
from src.generate_data import generate_transactions

BASE_COLS = ["invoice_id", "invoice_date", "customer_id", "product_id",
             "product_name", "category", "quantity", "unit_price",
             "unit_cost", "discount_pct", "branch", "region", "channel"]


def make_df(rows):
    df = pd.DataFrame(rows, columns=BASE_COLS)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    return df


def row(inv, date, cust, prod, name, qty, price, cost=0, disc=0.0):
    return [inv, date, cust, prod, name, "Cat", qty, price, cost, disc,
            "B1", "R1", "Online"]


# ------------------------------------------------------------------ cleaning
def test_cleaning_drops_each_bad_kind():
    good = row("HD1", "2024-01-01", "KH1", "SP1", "A", 2, 100)
    dirty = pd.DataFrame([
        good, good,  # trùng
        row("HD2", "2024-01-01", "KH1", "SP1", "A", 0, 100),      # qty = 0
        row("HD3", "2024-01-01", "KH1", "SP1", "A", -1, 100),     # qty âm
        row("HD4", "2024-01-01", None, "SP1", "A", 1, 100),       # thiếu khách
        row("HD5", "2024-01-01", "KH1", "SP1", "A", 1, 0),        # giá 0
        row("HD6", "not-a-date", "KH1", "SP1", "A", 1, 100),      # ngày lỗi
    ], columns=BASE_COLS)
    clean, rep = clean_transactions(dirty)
    assert rep["rows_in"] == 7 and rep["rows_out"] == 1
    assert rep["dropped_duplicates"] == 1
    assert rep["dropped_bad_quantity"] == 2
    assert rep["dropped_missing_id"] == 1
    assert rep["dropped_bad_price"] == 1
    assert rep["dropped_bad_date"] == 1
    # revenue dẫn xuất: 2 * 100 * (1-0) = 200
    assert clean.iloc[0]["revenue"] == 200


def test_schema_missing_column_raises():
    with pytest.raises(SchemaError) as e:
        validate_schema(pd.DataFrame({"invoice_id": [1]}))
    assert "customer_id" in str(e.value)


# ------------------------------------------------------------------ KPI
def test_kpi_and_aov_known():
    df, _ = clean_transactions(make_df([
        row("HD1", "2024-01-01", "KH1", "SP1", "A", 2, 100, cost=60),
        row("HD1", "2024-01-01", "KH1", "SP2", "B", 1, 300, cost=100),
        row("HD2", "2024-01-02", "KH1", "SP1", "A", 1, 500, cost=200),
        row("HD3", "2024-01-03", "KH2", "SP1", "A", 1, 1000, cost=500),
    ]))
    k = compute_kpi(df)
    assert k["revenue"] == 2000 and k["orders"] == 3 and k["customers"] == 2
    assert k["aov"] == pytest.approx(2000 / 3)
    assert k["profit"] == pytest.approx(2000 - (120 + 100 + 200 + 500))
    assert k["repeat_rate_pct"] == pytest.approx(50.0)  # KH1 quay lại, KH2 không


# ------------------------------------------------------------------ RFM
def test_rfm_known_values_and_segments():
    rows = []
    # KH_VIP: mua 10 lần, lần cuối sát snapshot, tổng lớn -> Champions
    for i in range(10):
        rows.append(row(f"V{i}", f"2024-12-{20 + i % 10}", "KH_VIP", "SP1", "A",
                        1, 1000, cost=500))
    # KH_CHURN: mua 3 lần đầu 2022 rồi thôi -> recency rất lớn
    for i in range(3):
        rows.append(row(f"C{i}", f"2022-01-0{i + 1}", "KH_CHURN", "SP1", "A",
                        1, 900, cost=500))
    # Thêm khách lấp đầy để quintile có ý nghĩa
    for k in range(8):
        for i in range(k % 4 + 1):
            rows.append(row(f"F{k}_{i}", "2024-06-15", f"KH_F{k}", "SP1", "A",
                            1, 100 + 50 * k, cost=50))
    df, _ = clean_transactions(make_df(rows))
    snap = pd.Timestamp("2025-01-01")
    rfm = compute_rfm(df, snapshot=snap).set_index("customer_id")
    vip = rfm.loc["KH_VIP"]
    assert vip["frequency"] == 10 and vip["monetary"] == 10000
    assert vip["recency"] == (snap - pd.Timestamp("2024-12-29")).days
    assert vip["segment"] == "Champions"
    churn = rfm.loc["KH_CHURN"]
    assert churn["recency"] > 1000
    assert churn["segment"] in ("Hibernating / Churned", "At Risk")


# ------------------------------------------------------------------ Basket
def test_basket_lift_known():
    rows = []
    # 10 giỏ: A luôn đi với B (5 giỏ), C xuất hiện độc lập 5 giỏ
    for i in range(5):
        rows.append(row(f"B{i}", "2024-01-01", "KH1", "SPA", "A", 1, 10))
        rows.append(row(f"B{i}", "2024-01-01", "KH1", "SPB", "B", 1, 10))
    for i in range(5, 10):
        rows.append(row(f"B{i}", "2024-01-01", "KH1", "SPC", "C", 1, 10))
    df, _ = clean_transactions(make_df(rows))
    pairs = basket_pairs(df, min_pair_count=1)
    ab = pairs[(pairs["product_a"] == "A") & (pairs["product_b"] == "B")].iloc[0]
    # support = 5/10 = 0.5; conf A->B = 1.0; lift = 1.0 / (5/10) = 2.0
    assert ab["support"] == pytest.approx(0.5)
    assert ab["confidence_a_to_b"] == pytest.approx(1.0)
    assert ab["lift"] == pytest.approx(2.0)


# ------------------------------------------------------------------ Churn label
def test_churn_label_definition():
    df, _ = clean_transactions(make_df([
        row("HD1", "2024-12-30", "KH_ACTIVE", "SP1", "A", 1, 100),
        row("HD2", "2024-01-01", "KH_GONE", "SP1", "A", 1, 100),
        row("HD3", "2024-06-01", "KH_GONE", "SP1", "A", 1, 100),
    ]))
    feat = build_customer_features(df, snapshot=pd.Timestamp("2025-01-01"))
    labelled = label_churn(feat, churn_window_days=120).set_index("customer_id")
    assert labelled.loc["KH_ACTIVE", "churned"] == 0   # mới mua 2 ngày trước
    assert labelled.loc["KH_GONE", "churned"] == 1     # lần cuối 214 ngày trước
    assert labelled.loc["KH_GONE", "recency"] == 214


# ------------------------------------------------------------------ Anomaly
def test_anomaly_flags_spike_month():
    monthly = pd.DataFrame({
        "month": [f"2024-{m:02d}" for m in range(1, 9)],
        "revenue": [100, 102, 98, 101, 99, 100, 200, 100],
        "profit": [10] * 8, "orders": [10] * 8,
    })
    flagged = detect_revenue_anomalies(monthly, threshold_pct=15.0)
    assert "2024-07" in set(flagged["month"])
    assert flagged.set_index("month").loc["2024-07", "direction"] == "Tăng mạnh"


# ------------------------------------------------------------------ Generator
def test_generator_reproducible_and_schema():
    d1 = generate_transactions(seed=123, start="2024-01-01", end="2024-03-31")
    d2 = generate_transactions(seed=123, start="2024-01-01", end="2024-03-31")
    assert len(d1) == len(d2) and len(d1) > 500
    c1, _ = clean_transactions(d1)
    c2, _ = clean_transactions(d2)
    assert c1["revenue"].sum() == c2["revenue"].sum()
    assert set(d1.columns) == set(BASE_COLS)
    assert d1["invoice_date"].min() >= pd.Timestamp("2024-01-01")
    # Cặp bán kèm phải tồn tại trong dữ liệu sinh ra
    pairs = basket_pairs(c1, min_pair_count=5)
    assert not pairs.empty and pairs["lift"].max() > 1.5
