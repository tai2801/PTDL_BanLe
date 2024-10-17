# EXPERIMENT RESULTS — Kết quả chạy trên dữ liệu mô phỏng

> Tất cả số dưới đây lấy từ lần chạy `python run_analysis.py` (seed 42)
> và nằm trong `outputs/` (`kpi_summary.json`, `report.md`, các CSV).
> Dữ liệu là MÔ PHỎNG — kết quả chứng minh pipeline đúng.

## 1. Dữ liệu & chất lượng
- 61.191 dòng vào → **60.948 dòng sạch**; loại 243 dòng (trùng 61,
  thiếu ID 61, số lượng lỗi 61, giá lỗi 60, ngày lỗi 0).
- Khoảng dữ liệu 2022-01-01 → 2024-12-31; 32.222 hóa đơn; 1.200 khách;
  42 sản phẩm; 79.501 mặt hàng bán ra.

## 2. KPI
| Chỉ số | Giá trị |
|---|---|
| Doanh thu | 72.511.813.550 đ |
| Lợi nhuận | 22.115.189.790 đ (biên 30,5%) |
| AOV | 2.250.382 đ |
| Tỉ lệ khách quay lại | 83,7% |
| Cơ cấu ngành | Điện tử 44,0% · Gia dụng 25,4% · Thể thao 11,9% · Thời trang 8,8% · Mỹ phẩm 5,2% · Thực phẩm 4,6% |
| SP doanh thu cao nhất | Laptop văn phòng — 8.268.625.000 đ |

## 3. Biến động doanh thu (ngưỡng 15%, trung bình trượt 3 tháng)
15 tháng bị gắn cờ. Đúng quy luật mùa vụ đã cài: tăng mạnh các tháng
11–12 (2022-12: **+33,6%**) và giảm mạnh tháng 2 sau Tết (2024-02:
**−33,1%**, 2023-02: −32,8%). Chi tiết: `outputs/revenue_anomalies.csv`.

## 4. Phân khúc RFM
| Segment | Khách | % khách | Doanh thu | % doanh thu |
|---|---|---|---|---|
| Champions | 260 | 21,7% | 36.124.538.150 đ | 49,8% |
| Loyal Customers | 181 | 15,1% | 12.866.514.850 đ | 17,7% |
| Potential Loyalists | 151 | 12,6% | 7.001.813.650 đ | 9,7% |
| At Risk | 128 | 10,7% | 7.572.280.700 đ | 10,4% |
| Need Attention | 116 | 9,7% | 4.362.666.400 đ | 6,0% |
| Hibernating / Churned | 358 | 29,8% | 4.370.750.350 đ | 6,0% |
| Cant Lose Them | 3 | 0,3% | 180.531.850 đ | 0,2% |
| New Customers | 3 | 0,3% | 32.717.600 đ | 0,0% |

Nhận xét có dẫn chứng: 21,7% khách (Champions) tạo 49,8% doanh thu;
nhóm At Risk còn giữ 7,57 tỉ đồng doanh thu lịch sử với recency trung
bình 275 ngày — mục tiêu win-back rõ ràng nhất.

## 5. Market Basket — kiểm chứng cặp bán kèm đã cài
| Cặp | Hóa đơn chung | Confidence | Lift |
|---|---|---|---|
| Tai nghe Bluetooth + Điện thoại tầm trung | 207 | 0,446 (ĐT→Tai nghe) | **11,46** |
| Loa Soundbar + Tivi 43 inch | 237 | 0,468 (Tivi→Loa) | **11,36** |
| Balo leo núi + Laptop văn phòng | 136 | 0,307 | 8,36 |
| Bộ nồi inox + Nồi chiên không dầu | 322 | 0,299 | 7,29 |
| Cáp HDMI 2m + Tivi 43 inch | 288 | 0,569 (Tivi→HDMI) | 7,28 |

Thuật toán tìm lại đúng cả 5/6 cặp đã cài vào dữ liệu với lift cao
nhất — bằng chứng pipeline basket hoạt động đúng (cặp còn lại nằm
ngoài top 5 hiển thị).

## 6. Churn (ngưỡng 120 ngày, split test 25%)
| Mô hình | Accuracy | ROC-AUC |
|---|---|---|
| Logistic Regression | 0,950 | 0,994 |
| Random Forest | **0,977** | **0,997** |

- Tỉ lệ rời bỏ theo nhãn: **28,8%** (346/1.200 khách) — khớp thiết kế
  (10% nhóm rời bỏ + khách mua một lần/thưa dần quá 120 ngày).
- Khách CHƯA rời bỏ nhưng nguy cơ cao (p ≥ 0,5): **4 khách**, doanh thu
  lịch sử bị đe dọa 105.683.900 đ (`outputs/churn_risk_customers.csv`).
- AUC rất cao vì nhãn là quy tắc theo recency và recency_ratio tương
  quan mạnh với nó — xem LIMITATIONS, không diễn giải là "mô hình
  gần hoàn hảo" trên dữ liệu thật.
