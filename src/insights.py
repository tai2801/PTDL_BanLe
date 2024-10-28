"""Sinh insight + khuyến nghị marketing.

NGUYÊN TẮC: mọi câu insight đều gắn con số tính từ dữ liệu thật truyền
vào. Không có số -> không sinh insight đó. Khuyến nghị theo phân khúc
cũng gắn quy mô (số khách, doanh thu) của chính phân khúc.
"""
from __future__ import annotations

import pandas as pd


def _fmt_money(v: float) -> str:
    return f"{v:,.0f} đ".replace(",", ".")


def build_insights(kpi: dict, segments: pd.DataFrame, anomalies: pd.DataFrame,
                   pairs: pd.DataFrame, churn_result: dict,
                   risk: pd.DataFrame, categories: pd.DataFrame,
                   df: pd.DataFrame) -> list[str]:
    out: list[str] = []

    top_seg = segments.sort_values("revenue", ascending=False).iloc[0]
    out.append(
        f"Phân khúc **{top_seg['segment']}** đóng góp doanh thu lớn nhất: "
        f"{_fmt_money(top_seg['revenue'])} ({top_seg['revenue_share_pct']:.1f}% tổng) "
        f"từ {int(top_seg['customers'])} khách ({top_seg['customer_share_pct']:.1f}% tổng khách).")

    # Tập trung doanh thu: top 10% khách theo monetary
    per_cust = df.groupby("customer_id")["revenue"].sum().sort_values(ascending=False)
    n_top = max(1, int(len(per_cust) * 0.10))
    share = per_cust.head(n_top).sum() / per_cust.sum() * 100
    out.append(
        f"10% khách hàng giá trị nhất ({n_top} khách) tạo ra {share:.1f}% doanh thu — "
        f"mức tập trung {'cao, cần chương trình giữ chân riêng' if share >= 40 else 'vừa phải'}.")

    out.append(
        f"Tỉ lệ khách quay lại mua lần 2+ là {kpi['repeat_rate_pct']:.1f}%; "
        f"giá trị đơn trung bình (AOV) {_fmt_money(kpi['aov'])}.")

    if not anomalies.empty:
        worst = anomalies.sort_values("deviation_pct").iloc[0]
        best = anomalies.sort_values("deviation_pct").iloc[-1]
        if worst["deviation_pct"] < 0:
            out.append(
                f"Doanh thu tháng {worst['month']} giảm mạnh {abs(worst['deviation_pct']):.1f}% "
                f"so với trung bình 3 tháng trước ({_fmt_money(worst['revenue'])} so với "
                f"{_fmt_money(worst['prev_avg'])}) — cần rà soát nguyên nhân theo chi nhánh/kênh.")
        if best["deviation_pct"] > 0:
            out.append(
                f"Doanh thu tháng {best['month']} tăng mạnh {best['deviation_pct']:.1f}% "
                f"({_fmt_money(best['revenue'])}) so với trung bình 3 tháng trước — "
                f"nên phân tích yếu tố thúc đẩy để lặp lại.")

    if not pairs.empty:
        p = pairs.iloc[0]
        out.append(
            f"Cặp sản phẩm mua cùng mạnh nhất: **{p['product_a']} + {p['product_b']}** "
            f"(lift {p['lift']:.2f}, xuất hiện cùng nhau trong {int(p['pair_invoices'])} hóa đơn) — "
            f"nên đặt kề nhau/gợi ý mua kèm.")

    out.append(
        f"Tỉ lệ khách đã rời bỏ (không mua > ngưỡng ngày cấu hình) là "
        f"{churn_result['churn_rate_pct']:.1f}% ({churn_result['n_churned']}/{churn_result['n_customers']} khách). "
        f"Có {len(risk)} khách CHƯA rời bỏ nhưng mô hình {churn_result['best_model']} "
        f"đánh giá nguy cơ cao, tổng doanh thu lịch sử của nhóm này là "
        f"{_fmt_money(risk['monetary'].sum()) if not risk.empty else '0 đ'} — doanh thu đang bị đe dọa.")

    top_cat = categories.iloc[0]
    out.append(
        f"Ngành hàng dẫn đầu: **{top_cat['category']}** chiếm {top_cat['revenue_share_pct']:.1f}% "
        f"doanh thu ({_fmt_money(top_cat['revenue'])}).")

    ch = (df.groupby("channel")["revenue"].sum())
    if len(ch) > 1:
        on = ch.get("Online", 0) / ch.sum() * 100
        out.append(f"Kênh Online chiếm {on:.1f}% doanh thu, Offline {100 - on:.1f}%.")
    return out


CAMPAIGN_TEMPLATES = {
    "Champions": "Giữ chân bằng ưu đãi sớm/ra mắt trước; nhóm này là nguồn doanh thu cốt lõi.",
    "Loyal Customers": "Chương trình tích điểm nâng hạng để kéo lên Champions.",
    "Cant Lose Them": "Chăm sóc 1-1 ngay (gọi điện/Zalo + voucher quay lại) — giá trị cao nhưng lâu chưa mua.",
    "At Risk": "Voucher quay lại có thời hạn 14 ngày + nhắc sản phẩm từng mua.",
    "Potential Loyalists": "Gợi ý mua kèm theo cặp sản phẩm lift cao để tăng tần suất.",
    "New Customers": "Chuỗi chào mừng + ưu đãi đơn thứ 2 trong 30 ngày để tạo thói quen.",
    "Need Attention": "Khảo sát ngắn + ưu đãi nhẹ kích hoạt lại.",
    "Hibernating / Churned": "Chiến dịch win-back chi phí thấp (email/Zalo hàng loạt), không dồn ngân sách chăm sóc 1-1.",
}


def segment_campaigns(segments: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in segments.iterrows():
        rows.append({
            "segment": r["segment"], "customers": int(r["customers"]),
            "revenue": float(r["revenue"]),
            "revenue_share_pct": float(r["revenue_share_pct"]),
            "avg_recency_days": float(r["avg_recency"]),
            "campaign": CAMPAIGN_TEMPLATES.get(r["segment"], "Chăm sóc định kỳ."),
        })
    return pd.DataFrame(rows)
