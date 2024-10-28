"""Chạy toàn bộ pipeline phân tích và xuất outputs/ + báo cáo Markdown."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import analytics as an
from . import basket as bk
from . import churn as ch
from . import insights as ins
from .cleaning import clean_transactions


def run_full_analysis(raw: pd.DataFrame, out_dir: str | Path,
                      churn_window_days: int = 120,
                      anomaly_threshold_pct: float = 15.0) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df, quality = clean_transactions(raw)

    kpi = an.compute_kpi(df)
    monthly = an.monthly_revenue(df)
    quarterly = an.quarterly_revenue(df)
    anomalies = an.detect_revenue_anomalies(monthly, threshold_pct=anomaly_threshold_pct)
    products = an.top_products(df, n=20)
    categories = an.category_summary(df)
    rfm = an.compute_rfm(df)
    segments = an.segment_summary(rfm)
    cohort = an.cohort_retention(df)
    pairs = bk.basket_pairs(df)
    feat = ch.label_churn(ch.build_customer_features(df), churn_window_days)
    churn_result = ch.train_churn_models(feat)
    risk = ch.high_risk_customers(churn_result["features"])
    campaigns = ins.segment_campaigns(segments)
    insight_list = ins.build_insights(kpi, segments, anomalies, pairs,
                                      churn_result, risk, categories, df)

    # ---- Xuất bảng tổng hợp
    monthly.to_csv(out / "monthly_revenue.csv", index=False)
    quarterly.to_csv(out / "quarterly_revenue.csv", index=False)
    anomalies.to_csv(out / "revenue_anomalies.csv", index=False)
    products.to_csv(out / "top_products.csv", index=False)
    categories.to_csv(out / "category_summary.csv", index=False)
    rfm.to_csv(out / "rfm_customers.csv", index=False)
    segments.to_csv(out / "rfm_segments.csv", index=False)
    cohort.to_csv(out / "cohort_retention.csv")
    pairs.to_csv(out / "basket_pairs.csv", index=False)
    risk.to_csv(out / "churn_risk_customers.csv", index=False)
    campaigns.to_csv(out / "segment_campaigns.csv", index=False)
    kpi_out = dict(kpi)
    kpi_out["data_quality"] = quality
    kpi_out["churn"] = {"window_days": churn_window_days,
                        "churn_rate_pct": churn_result["churn_rate_pct"],
                        "n_churned": churn_result["n_churned"],
                        "best_model": churn_result["best_model"],
                        "metrics": churn_result["metrics"],
                        "n_high_risk_active": int(len(risk)),
                        "revenue_at_risk": float(risk["monetary"].sum()) if not risk.empty else 0.0}
    with open(out / "kpi_summary.json", "w", encoding="utf-8") as f:
        json.dump(kpi_out, f, ensure_ascii=False, indent=2)

    # ---- Báo cáo Markdown có số thật
    lines = [
        "# BÁO CÁO PHÂN TÍCH BÁN LẺ (số liệu tính từ dữ liệu đầu vào)",
        "",
        f"- Khoảng dữ liệu: {kpi['date_from']} → {kpi['date_to']}",
        f"- Doanh thu: {kpi['revenue']:,.0f} đ · Lợi nhuận: {kpi['profit']:,.0f} đ "
        f"(biên {kpi['profit_margin_pct']:.1f}%)",
        f"- Tổng đơn: {kpi['orders']} · Khách: {kpi['customers']} · "
        f"AOV: {kpi['aov']:,.0f} đ · Tỉ lệ quay lại: {kpi['repeat_rate_pct']:.1f}%",
        f"- Chất lượng dữ liệu: {quality['rows_in']} dòng vào → {quality['rows_out']} dòng sạch "
        f"(loại {quality['dropped_total']}: trùng {quality['dropped_duplicates']}, "
        f"số lượng lỗi {quality['dropped_bad_quantity']}, thiếu ID {quality['dropped_missing_id']}, "
        f"giá lỗi {quality['dropped_bad_price']}, ngày lỗi {quality['dropped_bad_date']}).",
        "",
        "## Insight chính",
    ]
    lines += [f"{i + 1}. {s}" for i, s in enumerate(insight_list)]
    lines += ["", "## Mô hình rời bỏ (churn)"]
    for name, m in churn_result["metrics"].items():
        lines.append(f"- {name}: accuracy {m['accuracy']:.3f}, ROC-AUC {m['roc_auc']:.3f} (tập test 25%)")
    lines.append(f"- Mô hình tốt hơn theo ROC-AUC: {churn_result['best_model']}; "
                 f"tỉ lệ rời bỏ {churn_result['churn_rate_pct']:.1f}%.")
    lines += ["", "## Phân khúc RFM", segments.to_markdown(index=False),
              "", "## Chiến dịch đề xuất theo phân khúc",
              campaigns.to_markdown(index=False)]
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")

    return {"kpi": kpi, "quality": quality, "segments": segments,
            "churn": churn_result, "risk": risk, "insights": insight_list,
            "anomalies": anomalies, "pairs": pairs}
