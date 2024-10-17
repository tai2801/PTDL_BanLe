# DATASET DESCRIPTION — Retail Analytics Intelligence

> **Dữ liệu kèm theo dự án là dữ liệu MÔ PHỎNG 100%**, sinh bằng
> `src/generate_data.py` với seed cố định 42. Không có dữ liệu khách
> hàng thật nào được sử dụng. Khi có dữ liệu thật, chỉ cần import file
> CSV/Excel đúng schema dưới đây — toàn bộ phân tích giữ nguyên.

## Schema (13 cột bắt buộc)
| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| invoice_id | str | Mã hóa đơn (nhiều dòng chung 1 hóa đơn) |
| invoice_date | date | Ngày giao dịch |
| customer_id | str | Mã khách hàng |
| product_id / product_name | str | Sản phẩm |
| category | str | Ngành hàng |
| quantity | int > 0 | Số lượng |
| unit_price | number > 0 | Đơn giá bán (VNĐ) |
| unit_cost | number ≥ 0 | Giá vốn/đơn vị |
| discount_pct | 0–0.9 | Tỉ lệ giảm giá của dòng |
| branch / region | str | Chi nhánh / khu vực |
| channel | str | Online / Offline |

Cột dẫn xuất khi làm sạch: `revenue = quantity × unit_price × (1 − discount_pct)`,
`profit = revenue − quantity × unit_cost`.

## Quy mô bộ mô phỏng (seed 42)
- **61.191 dòng thô** (60.948 dòng sạch), **32.222 hóa đơn**, **1.200 khách**,
  **42 sản phẩm** thuộc **6 ngành hàng** (Điện tử, Gia dụng, Thời trang,
  Mỹ phẩm, Thực phẩm, Thể thao), **5 chi nhánh / 5 khu vực**, 2 kênh,
  khoảng **2022-01-01 → 2024-12-31**.

## Quy luật đã cài vào dữ liệu (để kiểm chứng phân tích)
1. **Mùa vụ:** hệ số tháng 1 = 1,30 (Tết), 11 = 1,30, 12 = 1,45; tháng
   6–7 = 0,85. Xu hướng tăng trưởng +12% trong 3 năm.
2. **Nhóm khách:** VIP 5% (mua ~2,6 đơn/tháng), Thường 50% (~0,85),
   Thỉnh thoảng 20% (~0,28), Rời bỏ 10% (ngừng mua sau một mốc ngẫu
   nhiên 06/2023–03/2024), Mua một lần 15% (đúng 1 hóa đơn).
3. **Sản phẩm bán kèm:** 6 cặp neo→kèm với xác suất kèm 0,28–0,55
   (vd Tivi→Loa Soundbar 0,45; Laptop→Chuột không dây 0,50) — market
   basket phải tìm ra các cặp này với lift cao.
4. **Dòng lỗi cố ý ~0,4%:** trùng dòng, quantity ≤ 0, thiếu customer_id,
   unit_price = 0 — bước làm sạch loại và đếm được (thực tế loại 243 dòng).

## File trong repo
- `data/sample_transactions.csv` — 1.000 dòng đầu của bộ mô phỏng (để
  xem schema và chạy thử nhanh).
- `data/transactions_full.csv` — bộ đầy đủ, **sinh lại bằng**
  `python run_analysis.py`, không đóng vào ZIP.
