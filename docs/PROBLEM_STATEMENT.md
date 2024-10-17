# PROBLEM STATEMENT & REQUIREMENTS

## Bài toán
Một chuỗi bán lẻ có dữ liệu giao dịch rời rạc theo ngày/chi nhánh/kênh
nhưng chỉ nhìn được "tổng doanh thu". Quản lý không trả lời được: doanh
thu tháng này lệch bất thường hay theo mùa? Khách nào giá trị nhất, khách
nào sắp rời bỏ? Sản phẩm nào hay được mua cùng nhau để trưng bày/gợi ý?
Hệ thống này biến dữ liệu giao dịch thô thành KPI, phân khúc khách hàng
và khuyến nghị hành động có số liệu dẫn chứng.

## Functional Requirements
- FR1: Import CSV/Excel theo schema chuẩn; thiếu cột → báo lỗi nêu rõ cột.
- FR2: Làm sạch dữ liệu, xuất báo cáo chất lượng (số dòng loại theo lý do).
- FR3: KPI doanh thu, lợi nhuận, số đơn, số khách, AOV, tỉ lệ khách quay lại.
- FR4: Doanh thu theo tháng/quý; gắn cờ tháng biến động vượt ngưỡng cấu hình.
- FR5: Top sản phẩm theo doanh thu/số lượng/lợi nhuận; cơ cấu ngành hàng.
- FR6: RFM segmentation (điểm ngũ phân vị) + CLV ước tính + cohort retention.
- FR7: Market basket: support/confidence/lift cho cặp sản phẩm mua cùng.
- FR8: Nhãn rời bỏ theo ngưỡng ngày cấu hình + mô hình ML dự đoán nguy cơ,
  có metrics trên tập test; danh sách khách nguy cơ cao chưa rời bỏ.
- FR9: Insight tự động kèm số; chiến dịch marketing đề xuất theo phân khúc.
- FR10: Dashboard lọc theo thời gian/khu vực/kênh; xuất CSV và báo cáo Markdown.

## Non-functional Requirements
- NFR1: Tái lập: cùng seed → cùng dữ liệu mô phỏng và cùng kết quả KPI.
- NFR2: Minh bạch: mọi công thức có trong METHODOLOGY.md; không insight
  nào không có số dẫn chứng.
- NFR3: Hiệu năng: pipeline ~61.000 dòng chạy < 1 phút trên máy thường.
- NFR4: Minh bạch dữ liệu: ghi rõ dữ liệu mô phỏng ở mọi đầu ra.
- NFR5: Test tự động cho từng công thức cốt lõi bằng dữ liệu biết trước đáp án.
