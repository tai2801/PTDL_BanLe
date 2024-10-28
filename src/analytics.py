"""Phân tích doanh thu, sản phẩm, RFM, CLV, cohort.

Mọi hàm nhận DataFrame ĐÃ làm sạch (có cột revenue, profit) và trả về
bảng tổng hợp — không hàm nào tự bịa số.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------- KPI
def compute_kpi(df: pd.DataFrame) -> dict:
    revenue = float(df["revenue"].sum())
    orders = int(df["invoice_id"].nunique())
    return {
        "revenue": revenue,
        "profit": float(df["profit"].sum()),
        "profit_margin_pct": float(df["profit"].sum() / revenue * 100) if revenue else 0.0,
        "orders": orders,
        "customers": int(df["customer_id"].nunique()),
        "products": int(df["product_id"].nunique()),
        "items_sold": int(df["quantity"].sum()),
        "aov": float(revenue / orders) if orders else 0.0,
        "avg_items_per_order": float(df.groupby("invoice_id")["quantity"].sum().mean()) if orders else 0.0,
        "repeat_rate_pct": repeat_rate(df),
        "date_from": str(df["invoice_date"].min().date()),
        "date_to": str(df["invoice_date"].max().date()),
    }


def repeat_rate(df: pd.DataFrame) -> float:
    """% khách có từ 2 hóa đơn trở lên."""
    per = df.groupby("customer_id")["invoice_id"].nunique()
    if len(per) == 0:
        return 0.0
    return float((per >= 2).mean() * 100)


# ---------------------------------------------------------------- Doanh thu theo thời gian
def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    m = (df.set_index("invoice_date").resample("ME")
           .agg(revenue=("revenue", "sum"), profit=("profit", "sum"),
                orders=("invoice_id", "nunique"))
           .reset_index())
    m["month"] = m["invoice_date"].dt.to_period("M").astype(str)
    return m[["month", "revenue", "profit", "orders"]]


def quarterly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    q = (df.assign(quarter=df["invoice_date"].dt.to_period("Q").astype(str))
           .groupby("quarter")
           .agg(revenue=("revenue", "sum"), profit=("profit", "sum"),
                orders=("invoice_id", "nunique"))
           .reset_index())
    q["qoq_pct"] = q["revenue"].pct_change() * 100
    return q


def detect_revenue_anomalies(monthly: pd.DataFrame,
                             window: int = 3,
                             threshold_pct: float = 15.0) -> pd.DataFrame:
    """Gắn cờ tháng có doanh thu lệch > threshold% so với trung bình trượt
    của `window` tháng liền trước. Trả về chỉ các tháng bất thường, kèm
    số liệu dẫn chứng (không kèm diễn giải bịa)."""
    m = monthly.copy()
    m["prev_avg"] = m["revenue"].shift(1).rolling(window).mean()
    m["deviation_pct"] = (m["revenue"] - m["prev_avg"]) / m["prev_avg"] * 100
    flagged = m[m["deviation_pct"].abs() > threshold_pct].copy()
    flagged["direction"] = np.where(flagged["deviation_pct"] > 0, "Tăng mạnh", "Giảm mạnh")
    return flagged[["month", "revenue", "prev_avg", "deviation_pct", "direction"]]


# ---------------------------------------------------------------- Sản phẩm
def top_products(df: pd.DataFrame, by: str = "revenue", n: int = 15) -> pd.DataFrame:
    g = (df.groupby(["product_id", "product_name", "category"])
           .agg(revenue=("revenue", "sum"), profit=("profit", "sum"),
                quantity=("quantity", "sum"), orders=("invoice_id", "nunique"))
           .reset_index())
    return g.sort_values(by, ascending=False).head(n).reset_index(drop=True)


def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = (df.groupby("category")
           .agg(revenue=("revenue", "sum"), profit=("profit", "sum"),
                quantity=("quantity", "sum"))
           .reset_index().sort_values("revenue", ascending=False))
    g["revenue_share_pct"] = g["revenue"] / g["revenue"].sum() * 100
    return g


# ---------------------------------------------------------------- RFM
def _quintile(series: pd.Series, invert: bool = False) -> pd.Series:
    """Chấm điểm 1-5 theo ngũ phân vị; dùng rank(method='first') để không
    lỗi khi nhiều giá trị trùng nhau ở biên."""
    ranks = series.rank(method="first")
    q = pd.qcut(ranks, 5, labels=[1, 2, 3, 4, 5]).astype(int)
    return 6 - q if invert else q


def compute_rfm(df: pd.DataFrame, snapshot: pd.Timestamp | None = None) -> pd.DataFrame:
    if snapshot is None:
        snapshot = df["invoice_date"].max() + pd.Timedelta(days=1)
    rfm = (df.groupby("customer_id")
             .agg(recency=("invoice_date", lambda s: (snapshot - s.max()).days),
                  frequency=("invoice_id", "nunique"),
                  monetary=("revenue", "sum"),
                  first_purchase=("invoice_date", "min"),
                  last_purchase=("invoice_date", "max"))
             .reset_index())
    rfm["r_score"] = _quintile(rfm["recency"], invert=True)
    rfm["f_score"] = _quintile(rfm["frequency"])
    rfm["m_score"] = _quintile(rfm["monetary"])
    rfm["segment"] = rfm.apply(_segment_of, axis=1)
    # CLV đơn giản (xem METHODOLOGY): doanh thu lịch sử + ước tính 12 tháng tới
    tenure_years = ((snapshot - rfm["first_purchase"]).dt.days / 365.25).clip(lower=0.1)
    rfm["purchases_per_year"] = rfm["frequency"] / tenure_years
    aov_cust = rfm["monetary"] / rfm["frequency"]
    rfm["clv_estimate"] = rfm["monetary"] + aov_cust * rfm["purchases_per_year"]
    return rfm


def _segment_of(r) -> str:
    r_s, f_s, m_s = int(r["r_score"]), int(r["f_score"]), int(r["m_score"])
    if r_s >= 4 and f_s >= 4 and m_s >= 4:
        return "Champions"
    if r_s == 1 and f_s >= 4 and m_s >= 4:
        return "Cant Lose Them"
    if f_s >= 4 and r_s >= 3:
        return "Loyal Customers"
    if r_s == 5 and f_s == 1:
        return "New Customers"
    if r_s >= 4 and 2 <= f_s <= 3:
        return "Potential Loyalists"
    if r_s == 3:
        return "Need Attention"
    if r_s <= 2 and f_s >= 3:
        return "At Risk"
    return "Hibernating / Churned"


def segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    g = (rfm.groupby("segment")
           .agg(customers=("customer_id", "count"), revenue=("monetary", "sum"),
                avg_clv=("clv_estimate", "mean"),
                avg_recency=("recency", "mean"), avg_frequency=("frequency", "mean"))
           .reset_index().sort_values("customers", ascending=False))
    g["customer_share_pct"] = g["customers"] / g["customers"].sum() * 100
    g["revenue_share_pct"] = g["revenue"] / g["revenue"].sum() * 100
    return g


# ---------------------------------------------------------------- Cohort
def cohort_retention(df: pd.DataFrame) -> pd.DataFrame:
    """Ma trận retention: hàng = tháng mua đầu tiên (cohort), cột = số tháng
    kể từ lần mua đầu, giá trị = % khách của cohort còn mua ở tháng đó."""
    d = df[["customer_id", "invoice_date"]].copy()
    d["month"] = d["invoice_date"].dt.to_period("M")
    first = d.groupby("customer_id")["month"].min().rename("cohort")
    d = d.join(first, on="customer_id")
    d["offset"] = (d["month"] - d["cohort"]).apply(lambda x: x.n)
    active = (d.groupby(["cohort", "offset"])["customer_id"].nunique()
                .unstack(fill_value=0))
    sizes = active[0].replace(0, np.nan)
    retention = (active.div(sizes, axis=0) * 100).round(1)
    retention.index = retention.index.astype(str)
    return retention
