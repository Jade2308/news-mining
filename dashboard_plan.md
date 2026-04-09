# Áp dụng Streamlit để tạo Dashboard Phân tích báo chí

Quá trình phân tích dữ liệu cho thấy hệ thống đã lưu trữ dữ liệu crawl và kết quả dự đoán (Clickbait/Non-clickbait) cũng như các chủ đề nóng (Hot Topics) vào cơ sở dữ liệu SQLite (`news.db`).
Mục tiêu là xây dựng một trang Dashboard bằng Streamlit phục vụ cho người dùng trực quan hoá các dữ liệu này theo thời gian thực (hoặc gần thực).

## 1. Thiết kế Giao diện (Streamlit App Layout)

Dashboard sẽ được chia thành 3 phần/tab chính:

### Tổng quan (Overview)
- **KPI Metrics:** Tổng số bài báo thu thập được, Số lượng bài clickbait vs non-clickbait, Tỷ lệ clickbait.
- **Biểu đồ:** Biểu đồ tỷ lệ (Pie chart) của clickbait; Biểu đồ số lượng bài báo được xuất bản/crawl theo thời gian.
- **Top Nguồn:** Bảng hoặc biểu đồ về nguồn cung cấp tin tức (VNExpress, Tuổi Trẻ,...).

### Chủ đề Nổi bật (Trending Topics)
- **Top Chủ đề:** Hiển thị danh sách các chủ đề từ bảng `hot_topics`, bao gồm các từ khóa, số lượng bài viết (`article_count`).
- **Word Cloud (nếu có thể):** Hiển thị từ khoá chính yếu của chủ đề nóng.
- **Bài viết trong chủ đề:** Khi người dùng chọn một chủ đề, liệt kê danh sách các bài báo thuộc chủ đề đó thông qua bảng `topic_articles`.

### Bộ lọc Clickbait (Clickbait Inspector)
- **Data Table:** Bảng dữ liệu tìm kiếm các bài báo, có cột filter theo `predicted_label` (Clickbait / Non-clickbait), cho phép tuỳ chọn theo `thresold` (Prediction Score).
- **Mẫu dự báo:** Hiển thị tiêu đề, đoạn tóm tắt, label dự đoán và nút mở link nội dung báo.

## 2. Chi Tiết Lấy Dữ Liệu và Sử Dụng Dữ Liệu (Data Query & Usage)

Để kết nối DB `news.db` và Streamlit, hệ thống sẽ sử dụng thư viện `sqlite3` kết hợp với `pandas` để load dữ liệu thành `DataFrame` nhằm tiện vẽ biểu đồ và hiển thị:

- **Truy xuất Tổng quan & Biểu đồ:**
  - Query: `SELECT source, predicted_label, prediction_score, crawled_at FROM articles WHERE predicted_label IS NOT NULL`
  - *Cách dùng:* Load vào `pandas.DataFrame`. Group by `source` để đếm bài theo nguồn. Tính tỷ lệ dòng `Clickbait` trên tổng số dòng. Nhóm theo giờ (`crawled_at`) để vẽ biểu đồ line chart số lượng cập nhật bài viết.
  
- **Truy xuất Chủ đề Nổi bật (Kèm lọc theo mốc thời gian):**
  - Trong Dashboard sẽ có một `st.selectbox` hoặc `st.radio` cho phép người dùng chọn mốc thời gian (vd: `1h`, `6h`, `12h`, `24h`, `1 tuần`). Giá trị trả về tương ứng quy đổi sang số giờ `timeframe_val`.
  - Query: `SELECT id, topic_name, keywords, article_count, created_at FROM hot_topics WHERE timeframe = ? ORDER BY created_at DESC, article_count DESC LIMIT 20` (với `?` là giá trị `timeframe_val` người dùng đã chọn, và lấy những topics được tính toán mới nhất).
  - Query bài cụ thể: `SELECT a.title, a.summary, a.url FROM articles a JOIN topic_articles ta ON a.article_id = ta.article_id WHERE ta.topic_id = ?`
  - *Cách dùng:* Tuỳ vào mốc thời gian người dùng chọn (1h, 6h, 24h,...), truy vấn DB sẽ filter `timeframe` tương ứng để lấy các chủ đề mới được detect trong khung giờ đó. Hiển thị danh sách top topics dưới dạng bảng, word cloud. Khi người dùng click chọn 1 chủ đề, chạy truy vấn thứ 2 để lấy các bài báo cụ thể.

- **Truy xuất Bộ lọc Clickbait:**
  - Query: `SELECT title, summary, url, source, prediction_score, predicted_label FROM articles WHERE predicted_label = ? ORDER BY crawled_at DESC LIMIT 100` (người dùng chọn label trên dashboard).
  - *Cách dùng:* Hiển thị dưới dạng `st.dataframe()` với tuỳ chọn sort/filter. Hiển thị điểm `prediction_score` và tuỳ chọn làm nổi bật các dòng có độ tin cậy thấp (dưới ngưỡng nào đó). Có thể tạo các thẻ (cards) bài báo sử dụng HTML+CSS để giao diện đẹp hơn thay vì dùng bảng khô khan.

## 3. Các Bước Triển Khai Thực Tế

- **Bước 1:** Tạo thư mục `dashboard/` và viết file `app.py`. Cấu hình cơ bản (Page config, Title).
- **Bước 2:** Cài đặt các thư viện bổ sung vào môi trường: `streamlit`, `pandas`, `plotly` (cho biểu đồ động), `wordcloud`.
- **Bước 3:** Tạo các hàm fetch dữ liệu trong `app.py` và sử dụng decorator `@st.cache_data(ttl=3600)` để lưu cache kết quả trong 1 giờ (phù hợp với crawler chạy 1 giờ/lần) nhằm tăng tốc độ tải trang.
- **Bước 4:** Xây dựng UI cho 3 tab như thiết kế.
- **Bước 5:** Thêm nút tắt cache/refresh bằng tay.
