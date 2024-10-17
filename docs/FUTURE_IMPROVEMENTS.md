# FUTURE IMPROVEMENTS — Retail Analytics Intelligence

1. **CLV xác suất:** thay heuristic bằng BG/NBD + Gamma-Gamma
   (thư viện `lifetimes`/BetaGeoFitter) khi có dữ liệu thật.
2. **Bất thường theo mùa vụ:** phân rã STL/seasonal decomposition
   trước khi gắn cờ để tháng sau Tết không bị báo động giả.
3. **Market basket nâng cao:** FP-Growth cho tập 3+ sản phẩm, basket
   theo khu vực/mùa, gợi ý sản phẩm theo khách (item-based CF).
4. **Churn theo thời gian:** huấn luyện trên cửa sổ trượt (train quá
   khứ, test tương lai) thay vì split ngẫu nhiên; thêm SHAP giải thích
   lý do từng khách nguy cơ cao.
5. **Dữ liệu lớn:** chuyển tầng phân tích sang Spark/DuckDB khi dữ
   liệu > 10⁶ dòng; vector hóa vòng lặp đặc trưng khách hàng.
6. **Vận hành:** lưu lịch sử import + phiên bản báo cáo, phân quyền
   Analyst/Manager, lên lịch chạy pipeline tự động.
7. **Dashboard:** thêm trang so sánh hai kỳ (YoY/MoM) và cảnh báo
   email/Zalo khi xuất hiện tháng bất thường mới.
