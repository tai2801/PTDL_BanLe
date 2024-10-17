# TEST REPORT — Retail Analytics Intelligence

Ngày chạy: 08/11/2024 · Môi trường: Windows 10, Python 3.11, numpy, pandas, scikit-learn, Streamlit, Plotly, pytest.

## 1. pytest — 8/8 PASS
```
python -m pytest tests/ -q   →   8 passed
```
| Test | Kiểm chứng |
|---|---|
| `test_cleaning_drops_each_bad_kind` | 7 dòng chứa đủ 5 loại lỗi → sạch còn 1; đếm đúng từng lý do; revenue dẫn xuất đúng |
| `test_schema_missing_column_raises` | Thiếu cột → `SchemaError` nêu tên cột |
| `test_kpi_and_aov_known` | Doanh thu 2.000, AOV = 2000/3, lợi nhuận, repeat 50% trên dữ liệu tính tay |
| `test_rfm_known_values_and_segments` | `KH_VIP`: F=10, M=10.000, recency đúng ngày → Champions; `KH_CHURN` recency > 1.000 ngày |
| `test_basket_lift_known` | Giỏ mẫu: support 0,5; confidence 1,0; lift đúng 2,0 |
| `test_churn_label_definition` | Khách mua 2 ngày trước → nhãn 0; 214 ngày → nhãn 1 (ngưỡng 120) |
| `test_anomaly_flags_spike_month` | Chuỗi tháng có spike ×2 → bị gắn cờ "Tăng mạnh" |
| `test_generator_reproducible_and_schema` | Cùng seed → cùng số dòng + cùng tổng doanh thu sau làm sạch; basket tìm thấy cặp kèm lift > 1,5 |

## 2. Pipeline đầy đủ
```
python run_analysis.py
→ 61.191 dòng mô phỏng; KPI doanh thu 72.511.813.550 đ; 32.222 đơn;
  1.200 khách; AOV 2.250.382 đ; repeat 83,7%
→ Churn: LR acc 0,950 / AUC 0,994; RF acc 0,977 / AUC 0,997;
  churn rate 28,8%; 4 khách nguy cơ cao, doanh thu bị đe dọa 105.683.900 đ
→ outputs/: 11 CSV + kpi_summary.json + report.md
```

## 3. Kiểm thử giao diện Streamlit — PASS
- `streamlit run app.py` khởi động, HTTP 200 tại `/`.
- Kiểm thử cả **6 trang** (Tổng quan, Doanh thu, Sản phẩm, Khách hàng & RFM, Giỏ hàng, Insight & Báo cáo): **0 exception**; KPI trên UI khớp `outputs/kpi_summary.json` (72.511.813.550 đ).
