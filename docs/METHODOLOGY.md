# METHODOLOGY — Công thức & định nghĩa

## KPI
- Doanh thu = Σ revenue của dòng sạch; Lợi nhuận = Σ profit.
- AOV (giá trị đơn trung bình) = Doanh thu / số hóa đơn distinct.
- Repeat rate = % khách có ≥ 2 hóa đơn.

## Phát hiện biến động doanh thu
Với mỗi tháng t: `prev_avg` = trung bình doanh thu 3 tháng liền trước;
`deviation% = (rev_t − prev_avg) / prev_avg × 100`. Tháng bị gắn cờ khi
`|deviation%| > ngưỡng` (mặc định 15%, chỉnh được trên dashboard).
Đây là phát hiện lệch theo quy tắc minh bạch, không phải mô hình thống
kê suy diễn — diễn giải nguyên nhân phải đối chiếu dữ liệu chi nhánh/kênh.

## RFM
Snapshot = ngày giao dịch cuối + 1 ngày.
- R (Recency) = số ngày từ lần mua cuối tới snapshot.
- F (Frequency) = số hóa đơn distinct. M (Monetary) = Σ revenue.
- Điểm 1–5 theo **ngũ phân vị trên hạng** (`rank(method='first')` rồi
  `qcut`) để không lỗi khi nhiều khách trùng giá trị; R đảo ngược
  (mới mua = điểm cao).

Phân khúc (kiểm tra theo thứ tự):
| Segment | Điều kiện |
|---|---|
| Champions | R≥4, F≥4, M≥4 |
| Cant Lose Them | R=1, F≥4, M≥4 |
| Loyal Customers | F≥4, R≥3 |
| New Customers | R=5, F=1 |
| Potential Loyalists | R≥4, 2≤F≤3 |
| Need Attention | R=3 |
| At Risk | R≤2, F≥3 |
| Hibernating / Churned | còn lại |

## CLV (đơn giản, có chủ đích)
`CLV ≈ Monetary + AOV_khách × số đơn/năm của khách`
trong đó số đơn/năm = F / max(tuổi khách theo năm, 0.1). Đây là ước
tính lịch sử + 12 tháng tới ở mức heuristic cho đồ án — không
phải mô hình CLV xác suất (BG/NBD), xem LIMITATIONS.

## Cohort retention
Cohort = tháng mua đầu tiên của khách. Ô (cohort, k) = % khách của
cohort có mua trong tháng thứ k kể từ lần mua đầu.

## Market Basket (tự cài bằng pandas)
Trên tập hóa đơn (mỗi hóa đơn = tập sản phẩm distinct):
- support(A,B) = |hóa đơn chứa A và B| / tổng hóa đơn
- confidence(A→B) = support(A,B) / support(A)
- lift(A,B) = confidence(A→B) / support(B); lift > 1 = mua cùng nhiều
  hơn ngẫu nhiên. Chỉ xét cặp có ≥ 10 hóa đơn chung (cấu hình được).

## Churn
- **Nhãn:** churned = 1 nếu Recency > `churn_window_days` (mặc định
  120 ngày, cấu hình được).
- **Đặc trưng (8):** frequency, monetary, AOV, tenure_days,
  unique_products, avg_gap_days (khoảng cách mua trung bình),
  **recency_ratio = recency / avg_gap_days**, promo_share.
  *Recency thô bị loại khỏi đặc trưng* vì nhãn suy trực tiếp từ nó —
  đưa vào là rò rỉ dữ liệu (leakage); recency_ratio vẫn giữ thông tin
  "đang trễ so với nhịp mua của chính khách đó" mà không lộ đáp án.
- **Mô hình:** Logistic Regression (chuẩn hóa StandardScaler) và
  Random Forest 200 cây; split stratified 75/25, random_state 42;
  đánh giá accuracy + ROC-AUC trên tập test.
- **Nguy cơ cao:** khách nhãn 0 (chưa rời bỏ) nhưng xác suất dự đoán
  ≥ 0,5 theo mô hình có AUC tốt hơn. "Doanh thu bị đe dọa" = Σ monetary
  lịch sử của nhóm này.
