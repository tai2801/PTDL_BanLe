# PROJECT OVERVIEW — Retail Analytics Intelligence

**Môn học:** Phân tích dữ liệu — HUIT.

## Tổng quan
Ứng dụng phân tích dữ liệu bán lẻ hoàn chỉnh: import giao dịch (CSV/Excel) → kiểm tra schema + làm sạch có báo cáo chất lượng → phân tích doanh thu, sản phẩm, hành vi khách hàng (RFM, CLV, cohort), market basket, dự đoán khách rời bỏ bằng Machine Learning → dashboard Streamlit tương tác và báo cáo xuất được (CSV/Markdown), trong đó **mọi insight đều gắn con số dẫn chứng tính từ chính dữ liệu đầu vào**.

## Điểm nổi bật của giải pháp
1. Là **ứng dụng Streamlit tương tác**: upload dữ liệu tự phục vụ, lọc theo thời gian/khu vực/kênh bán.
2. RFM + CLV + retention cohort + market basket tính **minh bạch bằng pandas**, công thức công khai trong `METHODOLOGY.md`.
3. **Phát hiện biến động doanh thu bất thường** theo ngưỡng cấu hình được (so với trung bình trượt 3 tháng).
4. Insight và **chiến dịch marketing theo phân khúc được sinh tự động từ kết quả phân tích kèm số liệu**.
5. Bộ dữ liệu mô phỏng có seed cố định và quy luật được tài liệu hóa rõ ràng.

## Kiến trúc tóm tắt
`src/generate_data.py` (sinh dữ liệu mô phỏng) → `src/cleaning.py` (validate + làm sạch) → `src/analytics.py` (KPI/RFM/CLV/cohort/bất thường), `src/basket.py` (support/confidence/lift), `src/churn.py` (nhãn + 2 mô hình ML) → `src/insights.py` (insight + chiến dịch) → `src/report.py` (xuất `outputs/`) và `app.py` (dashboard Streamlit).

## Công nghệ
Python 3.11+, pandas, numpy, scikit-learn, Streamlit, Plotly, pytest. Dữ liệu dạng CSV/Excel, kết quả tổng hợp dạng CSV/JSON/Markdown trong `outputs/`.
