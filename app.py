"""Retail Analytics Intelligence — Dashboard Streamlit.

Chạy:  streamlit run app.py
Dữ liệu mặc định: data/transactions_full.csv (MÔ PHỎNG) nếu có, không thì
data/sample_transactions.csv. Có thể upload CSV/Excel đúng schema mẫu ở sidebar.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from src import analytics as an  # noqa: E402
from src import basket as bk  # noqa: E402
from src import churn as ch  # noqa: E402
from src import insights as ins  # noqa: E402
from src.cleaning import SchemaError, clean_transactions, load_file  # noqa: E402

st.set_page_config(page_title="Retail Analytics Intelligence", layout="wide")
st.title("Retail Analytics Intelligence")
st.caption("Dữ liệu mặc định là dữ liệu MÔ PHỎNG có ghi rõ nguồn gốc — "
           "mọi con số trên trang đều tính trực tiếp từ dữ liệu đang nạp.")


@st.cache_data(show_spinner=False)
def load_default() -> pd.DataFrame:
    full = BASE / "data" / "transactions_full.csv"
    path = full if full.exists() else BASE / "data" / "sample_transactions.csv"
    return load_file(path)


def fmt(v: float) -> str:
    return f"{v:,.0f} đ".replace(",", ".")


# ------------------------------------------------------------------ Nguồn dữ liệu
with st.sidebar:
    st.header("Dữ liệu")
    uploaded = st.file_uploader("Import CSV/Excel giao dịch (đúng schema mẫu)",
                                type=["csv", "xlsx", "xls"])
    raw = None
    if uploaded is not None:
        try:
            raw = load_file(uploaded, filename=uploaded.name)
            st.success(f"Đã đọc {len(raw)} dòng từ file upload.")
        except SchemaError as e:
            st.error(str(e))
    if raw is None:
        raw = load_default()
    churn_window = st.slider("Ngưỡng rời bỏ (ngày không mua)", 30, 365, 120, 10)
    anomaly_threshold = st.slider("Ngưỡng biến động doanh thu (%)", 5, 50, 15, 1)

df_clean, quality = clean_transactions(raw)
st.sidebar.info(f"Chất lượng dữ liệu: {quality['rows_in']} dòng vào → "
                f"{quality['rows_out']} dòng sạch (loại {quality['dropped_total']}).")

# ------------------------------------------------------------------ Bộ lọc
with st.sidebar:
    st.header("Bộ lọc")
    dmin, dmax = df_clean["invoice_date"].min(), df_clean["invoice_date"].max()
    start, end = st.date_input("Khoảng ngày", (dmin.date(), dmax.date()))
    regions = st.multiselect("Khu vực", sorted(df_clean["region"].unique()),
                             default=sorted(df_clean["region"].unique()))
    channels = st.multiselect("Kênh bán", sorted(df_clean["channel"].unique()),
                              default=sorted(df_clean["channel"].unique()))

df = df_clean[(df_clean["invoice_date"].dt.date >= start)
              & (df_clean["invoice_date"].dt.date <= end)
              & (df_clean["region"].isin(regions))
              & (df_clean["channel"].isin(channels))]
if df.empty:
    st.warning("Không có dữ liệu với bộ lọc hiện tại.")
    st.stop()

kpi = an.compute_kpi(df)
monthly = an.monthly_revenue(df)
anomalies = an.detect_revenue_anomalies(monthly, threshold_pct=float(anomaly_threshold))

page = st.sidebar.radio("Trang", ["Tổng quan", "Doanh thu", "Sản phẩm",
                                  "Khách hàng & RFM", "Giỏ hàng",
                                  "Insight & Báo cáo"])

if page == "Tổng quan":
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Doanh thu", fmt(kpi["revenue"]))
    c2.metric("Lợi nhuận", fmt(kpi["profit"]), f"biên {kpi['profit_margin_pct']:.1f}%")
    c3.metric("Tổng đơn", f"{kpi['orders']:,}".replace(",", "."))
    c4.metric("Tổng khách", f"{kpi['customers']:,}".replace(",", "."))
    c5.metric("AOV", fmt(kpi["aov"]))
    st.plotly_chart(px.bar(monthly, x="month", y="revenue",
                           title="Doanh thu theo tháng"), use_container_width=True)
    if not anomalies.empty:
        st.subheader("Tháng biến động bất thường")
        st.dataframe(anomalies, use_container_width=True)

elif page == "Doanh thu":
    st.plotly_chart(px.line(monthly, x="month", y=["revenue", "profit"],
                            title="Doanh thu & lợi nhuận theo tháng"),
                    use_container_width=True)
    q = an.quarterly_revenue(df)
    st.plotly_chart(px.bar(q, x="quarter", y="revenue",
                           title="Doanh thu theo quý"), use_container_width=True)
    st.dataframe(q, use_container_width=True)
    st.subheader("Biến động bất thường (so trung bình trượt 3 tháng trước)")
    st.dataframe(anomalies if not anomalies.empty else
                 pd.DataFrame({"Thông báo": ["Không có tháng nào vượt ngưỡng."]}),
                 use_container_width=True)

elif page == "Sản phẩm":
    top = an.top_products(df, n=20)
    st.plotly_chart(px.bar(top.head(10).iloc[::-1], x="revenue", y="product_name",
                           orientation="h", title="Top 10 sản phẩm theo doanh thu"),
                    use_container_width=True)
    st.dataframe(top, use_container_width=True)
    cat = an.category_summary(df)
    st.plotly_chart(px.pie(cat, values="revenue", names="category",
                           title="Cơ cấu doanh thu theo ngành hàng"),
                    use_container_width=True)
    st.dataframe(cat, use_container_width=True)

elif page == "Khách hàng & RFM":
    rfm = an.compute_rfm(df)
    seg = an.segment_summary(rfm)
    st.subheader("Phân khúc RFM")
    st.dataframe(seg, use_container_width=True)
    st.plotly_chart(px.scatter(rfm, x="recency", y="frequency", size="monetary",
                               color="segment", hover_name="customer_id",
                               title="RFM: Recency x Frequency (cỡ = Monetary)"),
                    use_container_width=True)
    st.subheader("Top 20 khách theo CLV ước tính")
    st.dataframe(rfm.sort_values("clv_estimate", ascending=False)
                 [["customer_id", "recency", "frequency", "monetary",
                   "clv_estimate", "segment"]].head(20),
                 use_container_width=True)
    with st.expander("Cohort retention (%)"):
        st.dataframe(an.cohort_retention(df), use_container_width=True)
    st.subheader("Dự đoán rời bỏ")
    feat = ch.label_churn(ch.build_customer_features(df), churn_window)
    result = ch.train_churn_models(feat)
    mcols = st.columns(len(result["metrics"]))
    for col, (name, m) in zip(mcols, result["metrics"].items()):
        col.metric(name, f"AUC {m['roc_auc']:.3f}", f"acc {m['accuracy']:.3f}")
    st.write(f"Tỉ lệ rời bỏ theo nhãn (>{churn_window} ngày không mua): "
             f"**{result['churn_rate_pct']:.1f}%**. Mô hình tốt hơn: "
             f"**{result['best_model']}**.")
    risk = ch.high_risk_customers(result["features"])
    st.write(f"Khách CHƯA rời bỏ nhưng nguy cơ cao: **{len(risk)}** "
             f"(doanh thu lịch sử {fmt(risk['monetary'].sum()) if not risk.empty else '0 đ'}).")
    st.dataframe(risk.head(50), use_container_width=True)

elif page == "Giỏ hàng":
    pairs = bk.basket_pairs(df)
    st.subheader("Cặp sản phẩm thường mua cùng (support / confidence / lift)")
    st.dataframe(pairs, use_container_width=True)
    if not pairs.empty:
        top = pairs.head(10).copy()
        top["pair"] = top["product_a"] + " + " + top["product_b"]
        st.plotly_chart(px.bar(top.iloc[::-1], x="lift", y="pair", orientation="h",
                               title="Top 10 cặp theo lift"), use_container_width=True)

elif page == "Insight & Báo cáo":
    rfm = an.compute_rfm(df)
    seg = an.segment_summary(rfm)
    feat = ch.label_churn(ch.build_customer_features(df), churn_window)
    result = ch.train_churn_models(feat)
    risk = ch.high_risk_customers(result["features"])
    pairs = bk.basket_pairs(df)
    cats = an.category_summary(df)
    for s in ins.build_insights(kpi, seg, anomalies, pairs, result, risk, cats, df):
        st.markdown(f"- {s}")
    st.subheader("Chiến dịch đề xuất theo phân khúc")
    st.dataframe(ins.segment_campaigns(seg), use_container_width=True)
    st.subheader("Xuất báo cáo")
    st.download_button("Tải bảng phân khúc (CSV)",
                       seg.to_csv(index=False).encode("utf-8-sig"),
                       "rfm_segments.csv", "text/csv")
    st.download_button("Tải cặp giỏ hàng (CSV)",
                       pairs.to_csv(index=False).encode("utf-8-sig"),
                       "basket_pairs.csv", "text/csv")
    st.download_button("Tải danh sách nguy cơ rời bỏ (CSV)",
                       risk.to_csv(index=False).encode("utf-8-sig"),
                       "churn_risk_customers.csv", "text/csv")
    st.caption("Báo cáo Markdown đầy đủ + toàn bộ bảng tổng hợp: chạy "
               "`python run_analysis.py` (ghi vào thư mục outputs/).")
