# LIMITATIONS — Hạn chế

1. **Dữ liệu mô phỏng:** toàn bộ kết quả trong `outputs/` đến từ dữ
   liệu sinh có quy luật do nhóm tự cài (mùa vụ, nhóm khách, cặp bán
   kèm). Chúng chứng minh pipeline tính đúng, KHÔNG chứng minh điều
   gì về thị trường thật. Muốn kết luận kinh doanh phải chạy trên dữ
   liệu giao dịch thật.
2. **AUC churn rất cao (0,994–0,997) là hệ quả của nhãn quy tắc:**
   nhãn rời bỏ được định nghĩa bằng recency, và đặc trưng
   recency_ratio tương quan mạnh với recency. Trên dữ liệu thật (nhãn
   từ hành vi hủy dịch vụ/không gia hạn), metrics sẽ thấp hơn nhiều.
   Nhóm đã loại recency thô khỏi đặc trưng để tránh leakage trực tiếp,
   nhưng không loại được tương quan gián tiếp này.
3. **CLV là heuristic đơn giản** (lịch sử + nhịp mua 12 tháng), không
   phải mô hình xác suất BG/NBD + Gamma-Gamma; chỉ dùng để xếp hạng
   tương đối khách hàng.
4. **Phát hiện bất thường theo ngưỡng cố định** (lệch % so với trung
   bình trượt) nhạy với mùa vụ: tháng sau Tết gần như luôn bị gắn cờ
   giảm. Bản nâng cấp nên dùng phân rã mùa vụ (STL) trước khi gắn cờ.
5. **Market basket ở mức cặp 2 sản phẩm** và đếm trên toàn kỳ; chưa
   xét basket theo mùa/khu vực, chưa dùng FP-Growth cho tập > 2 món.
6. **Hiệu năng:** vòng lặp sinh dữ liệu theo ngày × khách và vòng lặp
   đặc trưng churn theo khách đủ nhanh cho ~10⁵ dòng; dữ liệu 10⁶+
   dòng cần vector hóa/chuyển Spark.
7. Dashboard chưa có phân quyền người dùng và chưa lưu lịch sử các
   lần import — phù hợp phạm vi đồ án, chưa phải sản phẩm vận hành.
