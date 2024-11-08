# Retail Analytics Intelligence — Phân tích doanh thu và hành vi khách hàng bán lẻ

Hệ thống **phân tích doanh thu và hành vi khách hàng** cho chuỗi bán lẻ:
KPI, doanh thu theo thời gian + phát hiện biến động bất thường, phân
khúc RFM, CLV, cohort retention, market basket (sản phẩm mua cùng),
dự đoán khách rời bỏ bằng Machine Learning, insight tự động kèm số
liệu và đề xuất chiến dịch marketing theo phân khúc.

> **Dữ liệu kèm theo là dữ liệu MÔ PHỎNG** (seed cố định, quy luật
> được ghi trong `docs/DATASET_DESCRIPTION.md`). Mọi con số trong
> `outputs/` đều tính từ dữ liệu đó bằng pipeline trong repo.

## Cài đặt
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Yêu cầu Python 3.11+. Phiên bản thư viện đã ghim trong
`requirements.txt` để đảm bảo tính tương thích ổn định khi chạy pipeline và dashboard.

## Chạy phân tích (CLI)
```bash
python run_analysis.py                 # sinh dữ liệu mô phỏng + phân tích -> outputs/
python run_analysis.py --input my.csv  # phân tích file giao dịch riêng (CSV/Excel)
python run_analysis.py --churn-window 90   # đổi ngưỡng rời bỏ (ngày)
```
Kết quả: `outputs/` gồm 11 bảng CSV (doanh thu tháng/quý, tháng bất
thường, top sản phẩm, RFM từng khách, phân khúc, cohort, cặp giỏ hàng,
khách nguy cơ rời bỏ, chiến dịch đề xuất), `kpi_summary.json` và
`report.md`.

**Kết quả mẫu (seed 42):** 61.191 dòng → doanh thu 72.511.813.550 đ,
32.222 đơn, 1.200 khách, AOV 2.250.382 đ; Champions = 21,7% khách tạo
49,8% doanh thu; churn: Random Forest accuracy 0,977 / ROC-AUC 0,997.

## Chạy dashboard
```bash
streamlit run app.py
```
6 trang: Tổng quan (KPI) · Doanh thu · Sản phẩm · Khách hàng & RFM
(+ CLV, cohort, churn) · Giỏ hàng · Insight & Báo cáo. Sidebar có bộ
lọc thời gian/khu vực/kênh, chỉnh ngưỡng rời bỏ + ngưỡng biến động,
và **upload CSV/Excel** dữ liệu riêng.

## Dùng dữ liệu thật của bạn
File cần đúng 13 cột (xem `docs/DATASET_DESCRIPTION.md`): invoice_id,
invoice_date, customer_id, product_id, product_name, category,
quantity, unit_price, unit_cost, discount_pct, branch, region,
channel. Thiếu cột hệ thống báo lỗi nêu rõ tên cột. Mẫu định dạng:
`data/sample_transactions.csv` (1.000 dòng mô phỏng).

## Kiểm thử
```bash
python -m pytest tests/ -q    # 8 test: làm sạch, KPI/AOV, RFM, lift, nhãn churn, bất thường, tái lập
```

## Cấu trúc
```
app.py                 Dashboard Streamlit
run_analysis.py        CLI chạy toàn pipeline
src/                   generate_data / cleaning / analytics / basket / churn / insights / report
data/                  sample_transactions.csv (bản đầy đủ sinh bằng run_analysis.py)
outputs/               Kết quả phân tích mẫu (CSV/JSON/report.md)
tests/                 pytest
docs/                  Overview, Problem+FR/NFR, Use Case, Architecture, Dataset,
                       Methodology, Experiment Results, Limitations, Test Report,
                       Future Improvements, References
```

## Tài khoản / bảo mật
Dự án không có tài khoản người dùng và không chứa mật khẩu/API key.
Dữ liệu mô phỏng không chứa thông tin cá nhân thật.

## Giấy phép
MIT License (xem `LICENSE`).
