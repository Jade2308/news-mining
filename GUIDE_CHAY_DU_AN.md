# TÀI LIỆU HƯỚNG DẪN CHUẨN: VẬN HÀNH DỰ ÁN CRAWL & PHÂN TÍCH TIN TỨC

Tài liệu này giải thích bản chất thực sự của các nhánh chức năng trong dự án, giúp bạn không bị lạc lối khi phải xử lý số lượng lớn mã nguồn.

---

## 🏗️ 1. Nguyên Tắc Hoạt Động Chung Của Hệ Thống

`news.db` là trái tim lưu trữ dữ liệu của bạn. Hệ thống này bao gồm 2 chu trình lớn:
- **Chu trình A (Thu thập / Crawl):** Lấy dữ liệu thô từ trang báo chép vào `news.db` với tình trạng "Nhãn = NULL".
- **Chu trình B (Gắn nhãn / Predict):** Bật Model Trí tuệ Nhân tạo (PhoBERT) lên, tìm các bài đang bị NULL trong `news.db`, đọc nội dung của nó rồi đóng mộc chữ `clickbait` hoặc `non-clickbait`.

> **Mẹo (Reset toàn bộ dự án):** Bạn chỉ cần xóa file `news.db`. Khi gọi lại bất kỳ lệnh Crawl nào ở phần 2, toàn bộ 2 Chu trình trên sẽ tự gầy dựng lại từ con số 0.

---

## 🚀 2. Bốn (4) Tệp Script Quan Trọng Nhất Định Phải Nhớ
Toàn bộ các file chạy của bạn đều nằm trong thư mục `scripts/`. Vui lòng mở Terminal và gõ đúng cú pháp bên dưới.

### 1️⃣ `python scripts/run_scheduler.py` (Khuyên dùng)
- **Tác dụng:** Trạm canh gác siêu thông minh. Nó tự động gọi hệ thống cào dữ liệu lên chạy **mỗi 60 phút 1 lần**. Điều hay nhất là hệ thống này sẽ dựa vào "đồng hồ thực tế" trên máy tính của bạn để bật ngủ - thức dậy theo đúng múi giờ đẹp (Ví dụ: `18:00:00`, `19:00:00`).
- **Nên dùng khi:** Máy đang cắm nạp điện, bạn muốn treo tool chạy chìm để hứng sự kiện thực tế 24/7. Cứ quăng Terminal ở đó, nó tự cào, tự bật Model lên đánh giá nhãn, rồi tự đi ngủ.

### 2️⃣ `python scripts/crawl_hourly.py`
- **Tác dụng:** Trinh sát tốc độ ánh sáng. Nó đi cào thông tin, nhưng nếu trên đường cào nó bốc trúng một cái tiêu đề mà DB đã có sẵn, nó sẽ hiểu ngay là *"Phần còn lại bị cũ hết rồi"* và **lập tức từ chối đi sâu xuống dưới**, chuyển qua báo mới ngay lập tức để tiết kiệm băng thông mạng.
- **Nên dùng khi:** Khi bạn nôn nóng muốn chọt tay lấy dữ liệu ngay mà không muốn ngồi chờ đồng hồ ở cái báo thức `run_scheduler` phía trên điểm chuông.

### 3️⃣ `python scripts/crawl_all.py`
- **Tác dụng:** Cỗ xe tăng càn quét thô ráp. Script này cũng đi lấy bài như số 2, nhưng thay vì quay lưng khi gặp trùng lặp, nó sẽ bỏ qua bài bị trùng đó nhưng **vẫn lếch thân xuống tận những bài dưới đáy sâu của trang** để cào véo cho bằng sạch không sót mảng bài nào mới thôi.
- **Nên dùng khi:** Lúc mới vừa reset/xóa `news.db` xong. Database đang trắng trơn, bạn cần cỗ xe tăng này tải đồ cổ nhiều nạc nhất có thể về xây nền móng Data khổng lồ.

### 4️⃣ `python scripts/label_articles_with_predictions.py`
- **Tác dụng:** Đây là công tắc kích hoạt "Bộ Náo" AI độc lập! Khi chạy file này, không có bất kỳ báo chắp nào bên ngoài bị cào. File sẽ tập trung RAM máy tính bật Model PhoBERT lên tìm mọi thứ đang để trống Nhãn trong DB để gắn bằng sạch (Bao gồm những bài bình thường, và gán tag `error_...` với những bài báo lỗi nhại lại để đỡ kẹt máy).
- **Nên dùng khi:** Đa số bạn không phải gọi nó! File số `1, 2 và 3` sau khi chạy xong bước cào đồ về thì chúng đã **tự tiện gọi giùm bạn** file số 4 này lên dọn dẹp nhãn luôn rồi. Chỉ dùng thủ công lúc nào bạn đổi thuật toán AI khác và muốn quét làm lại toàn bộ nhãn từ đầu.

---

## 🛠️ 3. Các Tool Hỗ Trợ Đóng Vai Trò Vi Chỉnh (Dành cho Tester)

- `python scripts/init_db.py`: Gọi thợ xây dựng bộ khung của cơ sở dữ liệu `news.db` (Giống như vẽ bản vẽ kiến trúc lúc mới bắt đầu chưa có DB).
- `python scripts/seed_db.py`: Bủa vây sâu cục bộ. Nếu bạn thấy thiếu hụt dữ liệu ở chuyên mục kinh tế, bạn gõ lệnh `python scripts/seed_db.py --source vnexpress --category kinh-doanh --limit 200` để nó ra lệnh tải mạnh 200 bài trong đó về bồi máu thêm cho bạn.

---

## 🤖 4. Xin Lưu Ý: Chuyển Dự Án Sang Máy Tính Mới (Vấn Đề Kẹt Model Lớn)

Thư mục chứa trí thông minh AI `models/phobert_clickbait/` sau khi huấn luyện xong có dung lượng rất lớn (thường lên đến hàng GB), do đó nó mặc định **không được phép đẩy lên GitHub** (do giới hạn lưu trữ của Git). Hệ quả là khi clone mã nguồn này về một cái máy tính mới, thư mục chứa AI của bạn sẽ bị mất tích hoàn toàn.

Cách để khôi phục và làm sống lại hệ thống AI tại máy tính mới:

**Bước 1: Tái tạo lại Trí thông minh gốc**
Tại khu vực gốc dự án, hãy mở Terminal lên và chạy file huấn luyện (Train) lại model:
```bash
python src/models/train_clickbait.py
```
*(Quá trình này sẽ tốn một khoảng thời gian chờ đợi tiến trình tùy thuộc vào năng lực máy tính. Hệ thống sẽ tự động học hỏi từ kho dữ liệu CSV có sẵn cấu trúc `clickbait_dataset_vietnamese.csv` của dự án để tái sinh lại nguyên bản thư mục `models/phobert_clickbait/` cho bạn rập khuôn y như cũ).*

**Bước 2: Gắn nhãn bù luồng dữ liệu bị tồn đọng**
Thông thường ở máy tính mới, CSDL của bạn có thể xuất hiện một đống bài được Crawl về mà chưa có nhãn. Hãy khởi động Model vừa mới rèn xong để nó vớt vát quét lại một lượt dự đoán bổ sung:
```bash
python scripts/label_articles_with_predictions.py
```

*(Sau khi xong 2 bước nền này, máy tính mới của bạn lại có quyền tiếp tục bật công cụ tự động `python scripts/run_scheduler.py` nhằm thảnh thơi cày cuốc như cũ).*
