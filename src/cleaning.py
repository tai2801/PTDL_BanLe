"""Kiểm tra schema + làm sạch dữ liệu giao dịch.

Dùng chung cho dữ liệu mô phỏng và file CSV/Excel người dùng tự import.
Mọi dòng bị loại đều được đếm theo lý do trong báo cáo chất lượng dữ liệu.
"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = [
    "invoice_id", "invoice_date", "customer_id", "product_id", "product_name",
    "category", "quantity", "unit_price", "unit_cost", "discount_pct",
    "branch", "region", "channel",
]


class SchemaError(ValueError):
    """File import thiếu cột bắt buộc hoặc không đọc được."""


def load_file(path_or_buffer, filename: str = "") -> pd.DataFrame:
    """Đọc CSV/Excel; raise SchemaError với thông báo rõ ràng nếu sai."""
    name = (filename or str(path_or_buffer)).lower()
    try:
        if name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(path_or_buffer)
        else:
            df = pd.read_csv(path_or_buffer)
    except Exception as exc:  # file hỏng / sai định dạng
        raise SchemaError(f"Không đọc được file: {exc}") from exc
    return validate_schema(df)


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise SchemaError(
            "File thiếu cột bắt buộc: " + ", ".join(missing) +
            f". Schema yêu cầu: {', '.join(REQUIRED_COLUMNS)}")
    return df[REQUIRED_COLUMNS].copy()


def clean_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Làm sạch và trả (df_sạch, báo cáo chất lượng).

    Thứ tự loại: trùng dòng -> ngày không hợp lệ -> thiếu khách/sản phẩm ->
    số lượng <= 0 -> đơn giá <= 0 -> giá vốn âm. Cột dẫn xuất:
    revenue = quantity * unit_price * (1 - discount_pct)
    profit  = revenue - quantity * unit_cost
    """
    report: dict = {"rows_in": int(len(df))}
    d = df.copy()

    n0 = len(d)
    d = d.drop_duplicates()
    report["dropped_duplicates"] = int(n0 - len(d))

    d["invoice_date"] = pd.to_datetime(d["invoice_date"], errors="coerce")
    n0 = len(d)
    d = d[d["invoice_date"].notna()]
    report["dropped_bad_date"] = int(n0 - len(d))

    n0 = len(d)
    d = d[d["customer_id"].notna() & d["product_id"].notna()
          & (d["customer_id"].astype(str).str.strip() != "")]
    report["dropped_missing_id"] = int(n0 - len(d))

    for col in ["quantity", "unit_price", "unit_cost", "discount_pct"]:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    d["discount_pct"] = d["discount_pct"].fillna(0).clip(0, 0.9)

    n0 = len(d)
    d = d[d["quantity"].notna() & (d["quantity"] > 0)]
    report["dropped_bad_quantity"] = int(n0 - len(d))

    n0 = len(d)
    d = d[d["unit_price"].notna() & (d["unit_price"] > 0)]
    report["dropped_bad_price"] = int(n0 - len(d))

    n0 = len(d)
    d = d[d["unit_cost"].notna() & (d["unit_cost"] >= 0)]
    report["dropped_bad_cost"] = int(n0 - len(d))

    d["quantity"] = d["quantity"].astype(int)
    d["revenue"] = d["quantity"] * d["unit_price"] * (1 - d["discount_pct"])
    d["profit"] = d["revenue"] - d["quantity"] * d["unit_cost"]
    d = d.sort_values("invoice_date").reset_index(drop=True)
    report["rows_out"] = int(len(d))
    report["dropped_total"] = report["rows_in"] - report["rows_out"]
    return d, report
