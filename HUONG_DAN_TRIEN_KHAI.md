# Hướng Dẫn Triển Khai (Deployment Guide)

Tài liệu này hướng dẫn chi tiết cách để clone dự án từ GitHub về một máy tính hoặc server rỗng và làm cho dự án chạy trơn tru từ A-Z, bao gồm cả luồng thu thập dữ liệu tự động và Streamlit Dashboard.

## Yêu cầu hệ thống (Prerequisites)
- **Python:** Phiên bản `>= 3.10`
- **Git** đã được cài đặt trên máy.
- **Dung lượng RAM:** Nên từ `4GB` trở lên (Khuyến nghị do cần train/load mô hình PhoBERT vào RAM).

---

## Các Bước Triển Khai

### Bước 1: Clone mã nguồn
Mở Terminal/Command Prompt tại nơi bạn muốn đặt thư mục dự án và chạy:
```bash
git clone <đường-link-github-của-repo-này>
cd ai-news-content-analysis
```

### Bước 2: Khởi tạo và kích hoạt môi trường ảo (Virtual Environment)
Việc sử dụng môi trường ảo giúp tránh xung đột thư viện với các dự án khác trên máy.
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Bước 3: Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```
*(Nếu làm Dashboard Streamlit, hãy cài thêm `pip install streamlit plotly wordcloud` nếu chưa có).*

### Bước 4: Thiết lập biến môi trường
Nếu dự án có sử dụng API key (như OpenAI) hay cấu hình riêng, bạn hãy sao chép file `.env.example` (nếu có) thành `.env`.
Hoặc có thể tự tạo file `.env` ở thư mục gốc:
```env
# Mở file .env lên và điền các khóa cấu hình cần thiết
OPENAI_API_KEY="sk-..."
```

### Bước 5: Khởi tạo Cơ sở Dữ liệu
Bạn cần tạo cấu trúc bảng (`news.db`) để hệ thống có nơi lưu trữ bài báo và chủ đề:
```bash
python scripts/init_db.py
```

### Bước 6: Tái tạo lại Trí Thông Minh (AI Model)
> **⚠️ Quan trọng:** Thư mục chứa mô hình `models/phobert_clickbait/` rất nặng (hàng GB) nên mặc định đã bị chặn bằng `.gitignore` và không được đưa lên GitHub.

Vì vậy mạng AI này bị xoá sạch khi mang sang máy mới. Để khôi phục nó, bạn phải bắt máy tính "học lại" một lần duy nhất bằng cách chạy lệnh:
```bash
python src/models/train_clickbait.py
```
*(Quá trình này tuỳ thuộc vào cấu hình máy, có thể mất từ 5 - 15 phút. Bạn chỉ cần chạy lệnh này một lần duy nhất).*

### Bước 7: Nạp dữ liệu ban đầu
Lúc này DB đang trống rỗng. Chạy cỗ xe tăng cào mọi thứ có thể để tạo "đáy" dữ liệu ban đầu cho Dashboard hoạt động được:
```bash
python scripts/crawl_all.py
```
*Ghi chú: Lệnh trên sẽ tự động thu thập tin → loại trùng lặp → và kích hoạt luôn bước đánh nhãn các tin bằng Model PhoBERT.*

---

## 🧠 Cách Chạy Từng Model Độc Lập Hoặc Toàn Bộ

Hệ thống cung cấp sẵn các scripts cho phép bạn chủ động chạy riêng lẻ từng Model xử lý dữ liệu:

### 1. Model Phân loại Clickbait (PhoBERT)
Nếu bạn chỉ muốn quét qua toàn bộ Database để AI gắn nhãn (Clickbait/Non-clickbait) cho những bài báo nào bị sót hoặc mới thêm vào:
```bash
python scripts/label_articles_with_predictions.py
```

### 2. Model Trích xuất Chủ đề Nóng (Topic Modeling - BERTopic/LLM)
Để yêu cầu hệ thống gom các bài viết thành các cụm chủ đề đang nổi tiếng:
```bash
python scripts/detect_hot_topics.py
```
Hoặc để tính toán lại Hot Topics cho **tất cả** các mốc thời gian (1h, 6h, 12h, 24h, 168h) và đưa gọn vào Database cho view Dashboard:
```bash
python scripts/run_all_timeframes.py
```

### 3. Model Khám phá Chuyên Mục mới
Dùng để quét và mở rộng hoặc nhận diện các Category (danh mục) báo chí tiềm năng:
```bash
python scripts/discover_categories.py
```

### 4. Chạy Tất Cả Toàn Bộ (Automated Pipeline)
Thay vì tự gõ lệnh chạy từng công đoạn Crawl & AI riêng lẻ bên trên, bạn hoàn toàn có thể uỷ quyền mọi thứ cho bộ lập lịch:
```bash
python scripts/run_scheduler.py
```
*(Cứ mỗi 60 phút hệ thống sẽ tự động Crawl bài báo mới, sau đó gọi mô hình Clickbait làm việc, tiếp tục gọi mô hình Topic Modeling, dọn dẹp sạch sẽ và lặp lại vòng lặp).*

---

## 🚀 Khởi Động Dashboard

Bây giờ bạn đã có đầy đủ mã nguồn, thư viện, mô hình AI và dữ liệu mẫu. Hãy bật giao diện tương tác lên:
```bash
streamlit run dashboard_plan.md  # Thay bằng `app.py` hay thư mục bạn sẽ code
```
_Mở URL local (vd: http://localhost:8501) hiển thị trên Terminal để trải nghiệm trực giác bằng giao diện._

---

## Thu thập dữ liệu liên tục (Cron Job / Background)

Để hệ thống luôn gần-thực-tế (near real-time) chạy trong lúc bạn đang ngủ:
```bash
python scripts/run_scheduler.py
```
Tiến trình này sẽ tự thức khuya dậy sớm dọn dẹp data và cào tin mỗi **60 phút một lần** theo đồng hồ thực của bạn.
