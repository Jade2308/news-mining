# Khai phá dữ liệu báo điện tử tiếng Việt theo thời gian gần thực phục vụ phân tích chủ đề và phát hiện clickbait

## news-mining – Module 1: Thu thập & Chuẩn hóa Dữ liệu

> **Web Mining** – Tự động thu thập, làm sạch và lưu trữ bài báo tiếng Việt từ VNExpress & Tuổi Trẻ vào SQLite.

---

## Hướng dẫn trình bày thuyết trình

### 1. Yêu cầu nội dung (5 ý bắt buộc)

- **Bài toán:** Xác định vấn đề và mục tiêu cần giải quyết.
- **Hướng làm:** Trình bày pipeline hoặc mô hình dự kiến.
- **Dữ liệu:** Nguồn lấy dữ liệu, cách thu thập và xử lý.
- **Baseline:** Chọn và trình bày một bài báo khoa học liên quan (ưu tiên paper mới nhất).
- **Kế hoạch thực hiện:** Lộ trình, phân chia công việc, timeline.

### 2. Tiêu chí đánh giá

| Tiêu chí                | Điểm | Mô tả                                                                 |
|-------------------------|------|-----------------------------------------------------------------------|
| Ý tưởng & Hướng làm     | 35   | Hiểu rõ bài toán, có quy trình, pipeline, phân chia công việc rõ ràng |
| Baseline (paper)        | 25   | Đọc, trình bày và áp dụng paper phù hợp cho bài toán                  |
| Dữ liệu & Tính khả thi  | 25   | Nguồn data rõ ràng, quy trình thu thập và xử lý hợp lý                |
| Tiến độ & Trình bày     | 15   | Trình bày mạch lạc, rõ ràng, đúng tiến độ                             |

**Mục đích:**  
- Đảm bảo ý tưởng đủ tính nghiên cứu, tránh đề tài quá đơn giản, quá rộng hoặc không khả thi.
- Bắt buộc có dữ liệu thật, baseline rõ ràng, định hướng kết quả đo lường được.

### 3. Phân công thành viên

#### 👤 Thành viên 1: Hiếu (phụ trách Mở & Kết)
- **Tìm hiểu:** Bối cảnh thực tế (tác hại clickbait, nhu cầu đọc tin sạch), cách lập kế hoạch dự án.
- **Slide cần làm:**
    - Slide tiêu đề & giới thiệu nhóm
    - Slide 1: Bài toán (vấn đề & mục tiêu)
    - Slide cuối: Kế hoạch thực hiện (timeline theo tuần)

#### 👤 Thành viên 2: ???? (phụ trách Dữ liệu)
- **Tìm hiểu:** Khảo sát các trang báo điện tử, sử dụng Python (BeautifulSoup/Selenium) để tự động thu thập tin mới, các bước làm sạch text (xóa HTML, loại bỏ trùng lặp).
- **Slide cần làm:**
    - Slide 2: Dữ liệu & tính khả thi (nguồn, công cụ, quy trình làm sạch)

#### 👤 Thành viên 3: ???? (phụ trách Paper Baseline)
- **Tìm hiểu:** Đọc tóm tắt paper "ViClickbait-2025", nắm số liệu chính: dataset 3414 mẫu, 31.2% là clickbait, định nghĩa clickbait.
- **Slide cần làm:**
    - Slide 3: Baseline (giới thiệu paper, thông số dữ liệu)
    - Slide 4: Cách áp dụng (sử dụng bộ data, công thức đo lường)

#### 👤 Thành viên 4: ???? (phụ trách Mô hình & Luồng hệ thống)
- **Tìm hiểu:** Các mô hình AI (PhoBERT nhận diện clickbait, BERTopic gom cụm chủ đề), luồng hệ thống từ thu thập đến hiển thị.
- **Slide cần làm:**
    - Slide 5: Hướng làm (pipeline/mô hình, sơ đồ tổng thể, thuật toán sử dụng)

---

## Cài đặt

```bash
pip install -r requirements.txt
```
> **Yêu cầu:** Python ≥ 3.10

---

## Khởi tạo cơ sở dữ liệu

```bash
python scripts/init_db.py
```
Tạo file `news.db` với schema chuẩn (nếu chưa tồn tại).  
> **Lưu ý:** Không commit `news.db` vào repo. Mỗi thành viên tự seed DB cục bộ.

---

## Seed dữ liệu

```bash
# Crawl VNExpress chuyên mục kinh-doanh, tối đa 200 bài
python scripts/seed_db.py --source vnexpress --category kinh-doanh --limit 200

# Crawl Tuổi Trẻ chuyên mục thời sự, tối đa 200 bài
python scripts/seed_db.py --source tuoitre --category thoi-su --limit 200

# Crawl tất cả nguồn với limit mặc định (50 bài mỗi nguồn)
python scripts/seed_db.py --source all --limit 50
```

### Tham số `seed_db.py`

| Tham số      | Mô tả                         | Mặc định                      |
|--------------|-------------------------------|-------------------------------|
| `--source`   | `vnexpress` / `tuoitre` / `all` | `all`                        |
| `--category` | Chuyên mục (tùy nguồn)        | `kinh-doanh` / `thoi-su`      |
| `--limit`    | Số bài tối đa mỗi nguồn       | `50`                          |
| `--db-path`  | Đường dẫn DB                  | `news.db` (từ `config.py`)    |

---

## Cấu trúc dự án

```
news-mining/
├── config.py                  # DB_PATH và cấu hình chung
├── requirements.txt
├── scripts/
│   ├── init_db.py             # Tạo DB & schema
│   └── seed_db.py             # Crawl → clean → insert
├── crawlers/
│   ├── base_crawler.py        # Abstract base
│   ├── vnexpress_crawler.py   # Crawler VNExpress
│   ├── tuoitre_crawler.py     # Crawler Tuổi Trẻ
│   └── utils.py               # normalize_text, parse_time
├── core/
│   └── types.py               # Article dataclass (unified schema)
├── processing/
│   └── clean_text.py          # Làm sạch nội dung HTML/text
└── database/
    ├── schema.py              # init_db() – CREATE TABLE
    └── db.py                  # insert_article, get_all_articles, …
```

---

## Schema bài báo (chuẩn hóa)

| Trường             | Kiểu   | Mô tả                                 |
|--------------------|--------|---------------------------------------|
| `article_id`       | TEXT   | sha1(url)                             |
| `url`              | TEXT   | URL bài gốc (UNIQUE)                  |
| `source`           | TEXT   | `vnexpress` / `tuoitre`               |
| `category`         | TEXT   | Chuyên mục                            |
| `title`            | TEXT   | Tiêu đề (bắt buộc)                    |
| `summary`          | TEXT   | Tóm tắt / sapo                        |
| `content_text`     | TEXT   | Nội dung đã làm sạch                  |
| `author`           | TEXT   | Tác giả                               |
| `tags`             | TEXT   | Tags (phân cách bằng dấu phẩy)        |
| `published_at`     | TEXT   | "YYYY-MM-DD HH:MM:SS" hoặc NULL       |
| `crawled_at`       | TEXT   | "YYYY-MM-DD HH:MM:SS"                 |
| `content_html_raw` | TEXT   | HTML gốc (debug)                      |
| `fingerprint`      | TEXT   | sha1(content_text chuẩn hóa)           |

---

## Lưu ý về Rate Limit & Điều khoản sử dụng

- VNExpress: delay **1 giây** giữa mỗi bài.
- Tuổi Trẻ: delay **0.5 giây** giữa mỗi bài.
- Không crawl quá nhanh, tuân thủ điều khoản sử dụng của các trang báo.
- Chỉ sử dụng cho mục đích nghiên cứu/học thuật.

---

## Không commit DB

`news.db` đã được thêm vào `.gitignore`.  
Mỗi thành viên tự chạy `init_db.py` và `seed_db.py` để tạo bản cục bộ.

---

## Slide Outline

### Slide 0: Tiêu đề (Mở đầu)

**Tên đề tài:** Khai phá dữ liệu báo điện tử tiếng Việt theo thời gian gần thực phục vụ phân tích chủ đề và phát hiện clickbait  
**Môn:** Chuyên đề 2 – Khai phá dữ liệu Web  
**GVHD:** [Điền tên Giảng viên]  
**Nhóm:** 4 thành viên [Điền tên các thành viên]  
**Từ khóa:** Near real-time (1h), Clickbait detection, Topic mining, Trending dashboard

---

### Slide 1: Bài toán & Output *(Tiêu chí: Bài toán – 35đ)*

**Thực trạng:**  
- Tin “giật tít” (clickbait) gây nhiễu, giảm trải nghiệm và chất lượng tiếp nhận thông tin.  
- Người đọc cần: lọc clickbait + nắm bắt chủ đề nóng theo thời gian.

**Mục tiêu hệ thống (2 nhiệm vụ song song):**  
1. Phát hiện & lọc clickbait từ tiêu đề/đoạn dẫn.  
2. Gom cụm và theo dõi chủ đề nóng (trending topics) từ các bài báo chất lượng.

**Định nghĩa “gần thực” (Near real-time):**  
- Cập nhật mỗi 60 phút (crawl interval = 1h).  
- Mục tiêu latency: bài đăng mới → lên dashboard trong ≤ ~1 giờ.

**Output cụ thể:**  
- **Clickbait:** label (clickbait/non-clickbait) + score (0–1) + ngưỡng lọc bài.  
- **Trending topics:** danh sách topic theo thời gian + top keywords + bài đại diện + biểu đồ xu hướng.

---

### Slide 2: Hướng làm & Pipeline tổng thể *(Tiêu chí: Pipeline/Model – 35đ)*

**Luồng xử lý (end-to-end):**  
1. **Collect URLs:** Trang mục / RSS (nếu có)  
2. **Fetch & Parse:** Requests + BeautifulSoup  
3. **Tiền xử lý:** Bỏ HTML/boilerplate, chuẩn hóa unicode, chuẩn hóa text  
4. **Chuẩn hóa thời gian:** publish_datetime theo chuẩn ISO 8601  
5. **Lưu trữ:** Database + logging  
6. **Dedup (Loại bỏ trùng lặp):**  
    - Theo url/title  
    - Kết hợp SimHash/MinHash cho title + lead_paragraph  
7. **Hai nhánh mô hình:**  
    - *Clickbait Detection:* PhoBERT fine-tune → label + score  
    - *Topic Modeling/Trending:* BERTopic hoặc LDA → topic/keywords/trend  
8. **Dashboard:**  
    - Trending topics theo thời gian  
    - Thống kê clickbait theo nguồn/chuyên mục

**Vận hành near real-time:**  
- Scheduler/cron chạy mỗi 60 phút  
- Crawl bền vững: retry/backoff, timeout, rate limit, user-agent  
- Thiết kế mở: có thể giảm chu kỳ (ví dụ 15 phút) chỉ bằng việc đổi cấu hình

> **Lưu ý:** Khi thuyết trình, cần chèn hình ảnh minh họa pipeline kiến trúc hệ thống vào slide này.

---

### Slide 3: Dữ liệu, nguồn & tính khả thi *(Tiêu chí: Data & Feasibility – 25đ)*

**Nguồn thu thập:**  
- 4 báo điện tử lớn: VnExpress, Tuổi Trẻ, Thanh Niên, Dân Trí  
- Cập nhật định kỳ mỗi 60 phút (near real-time)

**Schema dữ liệu (bám sát ViClickbait-2025):**  
- `id` (unique identifier)  
- `url` (link bài)  
- `title` (headline)  
- `lead_paragraph` (đoạn dẫn/tóm tắt nếu có)  
- `category` (chuyên mục)  
- `publish_datetime` (ISO 8601)  
- `source` (tên báo)  
- `thumbnail_url` (nếu có)  
- *(Tuỳ chọn)* `content` (hỗ trợ topic modeling tốt hơn)

**Tiền xử lý & Dedup:**  
- Loại bỏ HTML/boilerplate, chuẩn hóa unicode, loại ký tự rác  
- Dedup theo url/title + SimHash/MinHash trên title + lead_paragraph

**Tính khả thi:**  
- Sử dụng dữ liệu thật, cập nhật liên tục theo chu kỳ 1h  
- Công cụ Python phổ biến, dễ triển khai, hoàn toàn demo được trong thời gian môn học  
- Mở rộng nguồn báo dễ dàng theo dạng “module crawler theo từng site”

---

### Slide 4: Baseline từ bài báo khoa học *(Tiêu chí: Baseline paper – 25đ)*

**Paper baseline:**  
- “ViClickbait-2025: A comprehensive dataset for Vietnamese clickbait detection” (Data in Brief, 2025)

**Thông tin quan trọng từ Paper:**  
- Dataset gồm 3,414 tiêu đề  
- Tỷ lệ clickbait chiếm 31.2%  
- Độ tin cậy gán nhãn cao: Cohen’s Kappa = 0.822  
- Đặc trưng clickbait: tạo “khoảng trống tò mò”, dùng từ cảm xúc mạnh, cường điệu hoá...

**Ý nghĩa baseline:**  
- Có dataset chuẩn + định nghĩa rõ ràng → đảm bảo tính “research-level”  
- Là cơ sở vững chắc để huấn luyện và so sánh mô hình clickbait cho hệ thống

---

### Slide 5: Áp dụng baseline & Cách đánh giá *(Tiêu chí: Baseline + đo lường)*

**A. Nhánh Clickbait Detection (PhoBERT fine-tune):**  
- Training data: ViClickbait-2025  
- Inference: Chạy trên dữ liệu crawl mỗi 1h → xuất label + score  
- Metrics đánh giá: Precision, Recall, F1-score, confusion matrix  
- Mục tiêu: Mô hình đủ tốt để lọc bài clickbait trước khi đưa vào phân tích chủ đề

**B. Nhánh Topic Modeling & Trending (BERTopic/LDA):**  
- Input: Ưu tiên bài non-clickbait (đã được lọc từ nhánh A)  
- Trending: Rolling window 24 giờ, cập nhật mỗi 60 phút  
- Đánh giá:  
  - Đo lường Topic coherence (Cv/UMass)  
  - Đánh giá thủ công nhỏ (nhóm tự review một số topic) do không có ground-truth topic

---

### Slide 6: Kế hoạch thực hiện & phân công *(Tiêu chí: Kế hoạch – 15đ)*

**Timeline 6 tuần:**  
- **Tuần 1:** Chốt schema + Database + scheduler/logging  
- **Tuần 2:** Crawl & lưu dữ liệu 4 báo (xử lý retry/rate-limit, đảm bảo ổn định)  
- **Tuần 3:** Preprocess + dedup (url/title + SimHash/MinHash)  
- **Tuần 4:** Train/eval mô hình PhoBERT clickbait (Precision/Recall/F1) + tích hợp inference  
- **Tuần 5:** Triển khai Topic modeling + trending (24h window) + đo lường coherence/review  
- **Tuần 6:** Xây dựng Dashboard + test end-to-end + chuẩn bị demo & báo cáo

**Phân công 4 thành viên:**  
- Thành viên 1: Xây dựng Crawler + scheduler/cron + logging  
- Thành viên 2: Preprocessing + thiết kế schema DB + thuật toán dedup  
- Thành viên 3: Phụ trách Clickbait model (PhoBERT) + evaluation (F1/PR/RC)  
- Thành viên 4: Phụ trách Topic/trending + làm dashboard + tích hợp hệ thống để demo

**Tóm tắt 3 giá trị cốt lõi của đề tài:**  
1. **Research-level:** Có baseline paper rõ ràng + mô hình chuẩn + metrics đánh giá minh bạch  
2. **Khả thi:** Vận hành near real-time 1h, scope dự án vừa sức để hoàn thiện trong 6 tuần  
3. **Data thật & Đo lường được:** Đánh giá F1 cho clickbait + coherence cho topic + có sản phẩm demo dashboard thực tế

---