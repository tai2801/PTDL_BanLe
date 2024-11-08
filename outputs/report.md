# BÁO CÁO PHÂN TÍCH BÁN LẺ (số liệu tính từ dữ liệu đầu vào)

- Khoảng dữ liệu: 2022-01-01 → 2024-12-31
- Doanh thu: 72,511,813,550 đ · Lợi nhuận: 22,115,189,790 đ (biên 30.5%)
- Tổng đơn: 32222 · Khách: 1200 · AOV: 2,250,382 đ · Tỉ lệ quay lại: 83.7%
- Chất lượng dữ liệu: 61191 dòng vào → 60948 dòng sạch (loại 243: trùng 61, số lượng lỗi 61, thiếu ID 61, giá lỗi 60, ngày lỗi 0).

## Insight chính
1. Phân khúc **Champions** đóng góp doanh thu lớn nhất: 36.124.538.150 đ (49.8% tổng) từ 260 khách (21.7% tổng khách).
2. 10% khách hàng giá trị nhất (120 khách) tạo ra 37.0% doanh thu — mức tập trung vừa phải.
3. Tỉ lệ khách quay lại mua lần 2+ là 83.7%; giá trị đơn trung bình (AOV) 2.250.382 đ.
4. Doanh thu tháng 2024-02 giảm mạnh 33.1% so với trung bình 3 tháng trước (1.681.788.250 đ so với 2.515.378.667 đ) — cần rà soát nguyên nhân theo chi nhánh/kênh.
5. Doanh thu tháng 2022-12 tăng mạnh 33.6% (3.018.863.800 đ) so với trung bình 3 tháng trước — nên phân tích yếu tố thúc đẩy để lặp lại.
6. Cặp sản phẩm mua cùng mạnh nhất: **Tai nghe Bluetooth + Điện thoại tầm trung** (lift 11.46, xuất hiện cùng nhau trong 207 hóa đơn) — nên đặt kề nhau/gợi ý mua kèm.
7. Tỉ lệ khách đã rời bỏ (không mua > ngưỡng ngày cấu hình) là 28.8% (346/1200 khách). Có 4 khách CHƯA rời bỏ nhưng mô hình Random Forest đánh giá nguy cơ cao, tổng doanh thu lịch sử của nhóm này là 105.683.900 đ — doanh thu đang bị đe dọa.
8. Ngành hàng dẫn đầu: **Điện tử** chiếm 44.0% doanh thu (31.935.173.300 đ).
9. Kênh Online chiếm 38.5% doanh thu, Offline 61.5%.

## Mô hình rời bỏ (churn)
- Logistic Regression: accuracy 0.950, ROC-AUC 0.994 (tập test 25%)
- Random Forest: accuracy 0.977, ROC-AUC 0.997 (tập test 25%)
- Mô hình tốt hơn theo ROC-AUC: Random Forest; tỉ lệ rời bỏ 28.8%.

## Phân khúc RFM
| segment               |   customers |     revenue |     avg_clv |   avg_recency |   avg_frequency |   customer_share_pct |   revenue_share_pct |
|:----------------------|------------:|------------:|------------:|--------------:|----------------:|---------------------:|--------------------:|
| Hibernating / Churned |         358 | 4.37075e+09 | 1.75183e+07 |     395.799   |         5.95531 |             29.8333  |           6.02764   |
| Champions             |         260 | 3.61245e+10 | 1.85931e+08 |       7.96154 |        54.3423  |             21.6667  |          49.8188    |
| Loyal Customers       |         181 | 1.28665e+10 | 9.55012e+07 |      23.8895  |        36.8122  |             15.0833  |          17.744     |
| Potential Loyalists   |         151 | 7.00181e+09 | 6.26615e+07 |       9.56954 |        23.0397  |             12.5833  |           9.6561    |
| At Risk               |         128 | 7.57228e+09 | 7.94346e+07 |     274.773   |        28.1875  |             10.6667  |          10.4428    |
| Need Attention        |         116 | 4.36267e+09 | 5.1221e+07  |      31.6379  |        17.9914  |              9.66667 |           6.01649   |
| Cant Lose Them        |           3 | 1.80532e+08 | 8.0355e+07  |     388       |        36.3333  |              0.25    |           0.248969  |
| New Customers         |           3 | 3.27176e+07 | 2.25475e+07 |       5.66667 |         5       |              0.25    |           0.0451204 |

## Chiến dịch đề xuất theo phân khúc
| segment               |   customers |     revenue |   revenue_share_pct |   avg_recency_days | campaign                                                                                   |
|:----------------------|------------:|------------:|--------------------:|-------------------:|:-------------------------------------------------------------------------------------------|
| Hibernating / Churned |         358 | 4.37075e+09 |           6.02764   |          395.799   | Chiến dịch win-back chi phí thấp (email/Zalo hàng loạt), không dồn ngân sách chăm sóc 1-1. |
| Champions             |         260 | 3.61245e+10 |          49.8188    |            7.96154 | Giữ chân bằng ưu đãi sớm/ra mắt trước; nhóm này là nguồn doanh thu cốt lõi.                |
| Loyal Customers       |         181 | 1.28665e+10 |          17.744     |           23.8895  | Chương trình tích điểm nâng hạng để kéo lên Champions.                                     |
| Potential Loyalists   |         151 | 7.00181e+09 |           9.6561    |            9.56954 | Gợi ý mua kèm theo cặp sản phẩm lift cao để tăng tần suất.                                 |
| At Risk               |         128 | 7.57228e+09 |          10.4428    |          274.773   | Voucher quay lại có thời hạn 14 ngày + nhắc sản phẩm từng mua.                             |
| Need Attention        |         116 | 4.36267e+09 |           6.01649   |           31.6379  | Khảo sát ngắn + ưu đãi nhẹ kích hoạt lại.                                                  |
| Cant Lose Them        |           3 | 1.80532e+08 |           0.248969  |          388       | Chăm sóc 1-1 ngay (gọi điện/Zalo + voucher quay lại) — giá trị cao nhưng lâu chưa mua.     |
| New Customers         |           3 | 3.27176e+07 |           0.0451204 |            5.66667 | Chuỗi chào mừng + ưu đãi đơn thứ 2 trong 30 ngày để tạo thói quen.                         |