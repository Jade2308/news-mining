# TÀI LIỆU HƯỚNG DẪN CHUẨN: VẬN HÀNH DỰ ÁN CRAWL & PHÂN TÍCH TIN TỨC

Tài liệu này giải thích bản chất thực sự của các công cụ trong dự án, giúp bạn vận hành hệ thống một cách trơn tru nhất.

---

## 🏗️ 1. Nguyên Tắc Hoạt Động Chung Của Hệ Thống

`news.db` là trái tim lưu trữ dữ liệu của bạn. Hệ thống bao gồm 2 chu trình lớn:
- **Chu trình A (Thu thập / Crawl):** Lấy dữ liệu thô từ trang báo chép vào `news.db` với tình trạng "Nhãn = NULL".
- **Chu trình B (Gắn nhãn / Predict):** Sử dụng mô hình AI (PhoBERT) để tìm các bài chưa có nhãn trong `news.db`, phân tích nội dung và đánh dấu là `clickbait` hoặc `non-clickbait`.

> [!TIP]
> **Reset toàn bộ dự án:** Bạn chỉ cần xóa file `news.db`. Khi chạy lại lệnh Crawl, hệ thống sẽ tự động khởi tạo lại cơ sở dữ liệu từ đầu.

---

## 🚀 2. Các Script Quan Trọng Nhất Định Phải Nhớ

Toàn bộ các tệp thực thi nằm trong thư mục `scripts/`. Hãy sử dụng Terminal để chạy các lệnh sau:

### 1️⃣ `python scripts/scheduler.py` (Khuyên dùng)
- **Tác dụng:** Trạm canh gác tự động. Nó sẽ kích hoạt việc cào dữ liệu **mỗi 60 phút một lần**. Hệ thống dựa vào thời gian thực để thực hiện công việc đúng vào đầu mỗi giờ (ví dụ: `18:00:00`, `19:00:00`).
- **Khi nào dùng:** Khi bạn muốn treo máy để hệ thống tự động thu thập và phân tích tin tức 24/7 mà không cần can thiệp thủ công.

### 2️⃣ `python scripts/crawl.py`
Đây là công cụ thu thập tin tức chính, hỗ trợ hai chế độ:
- `--hourly`: **Chế độ nhanh.** Chỉ lấy các bài mới nhất và dừng lại ngay khi gặp bài đã có trong database. Tiết kiệm băng thông và thời gian.
- `--full`: **Chế độ càn quét.** Thu thập tất cả các bài viết hiện có trên các chuyên mục, kể cả các bài cũ.
- **Ví dụ:** `python scripts/crawl.py --hourly` hoặc `python scripts/crawl.py --full`.

### 3️⃣ `python scripts/label_articles.py`
- **Tác dụng:** Kích hoạt "Bộ não" AI độc lập. Script này sẽ quét toàn bộ database và gắn nhãn cho các bài viết còn trống.
- **Khi nào dùng:** Thông thường các lệnh crawl đã tự động gọi script này. Bạn chỉ chạy thủ công khi muốn cập nhật lại nhãn sau khi thay đổi mô hình AI hoặc xử lý các bài viết bị sót.

---

## 🛠️ 3. Công Cụ Quản Lý Dữ Liệu (`db_tool.py`)

Đây là công cụ đa năng để quản lý database `news.db`:

- `python scripts/db_tool.py check`: Kiểm tra trạng thái hiện tại của database (số lượng bài viết, thống kê theo nguồn, chuyên mục...).
- `python scripts/db_tool.py init`: Khởi tạo cấu trúc database mới.
- `python scripts/db_tool.py seed`: Nạp dữ liệu mồi.
    - *Ví dụ:* `python scripts/db_tool.py seed --source vnexpress --limit 100`

---

## 🔍 4. Công Cụ Truy Vấn (`query_db.py`)

- `python scripts/query_db.py`: Giúp bạn xem nhanh các bài viết mới nhất, tìm kiếm từ khóa hoặc xem thống kê chi tiết mà không cần mở phần mềm quản lý database chuyên dụng.

---

## 🤖 5. Lưu Ý Khi Chuyển Sang Máy Tính Mới

Thư mục mô hình AI `models/phobert_clickbait/` có dung lượng rất lớn nên thường không được đưa lên Git. Khi clone dự án về máy mới, bạn cần khôi phục mô hình:

**Bước 1: Huấn luyện lại mô hình**
```bash
python -m ai_news.models.train_clickbait
```
*(Hệ thống sẽ học từ file `data/clickbait_dataset_vietnamese.csv` để tái tạo lại mô hình).*

**Bước 2: Gắn nhãn cho dữ liệu hiện có**
```bash
python scripts/label_articles.py
```

Sau khi hoàn tất, bạn có thể bắt đầu sử dụng `python scripts/scheduler.py` như bình thường.
