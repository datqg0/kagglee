# 🌾 Kaggriculture Web Arena & Visualizer

Hệ thống Web App mô phỏng và xem trực quan các trận đấu AI của cuộc thi **Kaggle Kaggriculture**, hoàn toàn chạy trong trình duyệt (Client-side WebAssembly với Pyodide) và sẵn sàng deploy lên **Vercel** miễn phí 100%.

---

## 🚀 Tính Năng Nổi Bật

1. **Đấu Trực Tiếp 2 Agent (Head-to-Head Arena):**
   - Hỗ trợ tải lên file `agent.py` qua kéo thả hoặc file picker.
   - Soạn thảo hoặc sửa code Python trực tiếp trên trình duyệt.
   - Tích hợp sẵn 5 agent mẫu:
     - `main.py`: Grandmaster Melon Surge + 50+ Strawberry Factory ($75,000 - $130,000+).
     - `abc.py`: Adaptive Market Liquidation & Town Shop Detector.
     - `starter.py`: Baseline Carrot Loop chuẩn của Kaggle.
     - `random.py`: Random action exploration.
     - `pass.py`: No-op baseline.

2. **Trình Mô Phỏng WebAssembly Tốc Độ Cao (Pyodide Worker):**
   - Chạy 720 turns (30 ngày nông nghiệp) chỉ trong ~1.5 - 3 giây.
   - Hiển thị tiến trình thời gian thực (0..100%, Ngày 01..30) và live score ticker.
   - Không bị timeout, không tốn server backend.

3. **Bảng Phân Tích Trận Đấu (Analytics Dashboard):**
   - Banner người chiến thắng, chênh lệch tiền và ROI.
   - Biểu đồ tăng trưởng tài sản theo 30 ngày (Canvas chart so sánh 2 người chơi).
   - Bảng thống kê: Lượt thu hoạch, Lệnh chợ, Số Farmhand thuê, Đất mở rộng, Lỗi exception.

4. **Trình Xem Replay Tương Tác 100% Giống Kaggle:**
   - Sử dụng trọn bộ sprite pixel-art gốc: Nông dân, Farmhand, Cây trồng các giai đoạn, Động vật, Chợ và Biểu đồ Sparkline giá cả, Cửa hàng Town.
   - Điều khiển lượt (Play, Pause, Step Next/Prev, Speed 0.5x – 20x, Day Scrubber).
   - Xuất file `.html` Standalone mở offline bất cứ lúc nào.
   - Xuất file `.json` và Tải file replay cũ lên để xem lại.

---

## 💻 Chạy Cục Bộ (Local Testing)

Mở terminal tại thư mục này và khởi động server HTTP bất kỳ (ví dụ Python):

```bash
# Sử dụng Python HTTP Server có sẵn
python -m http.server 8000
```

Sau đó mở trình duyệt và truy cập: `http://localhost:8000`

---

## 🌐 Hướng Dẫn Deploy Lên Vercel (1-Click Deploy)

Vì ứng dụng hoàn toàn là **Static Web App (HTML/CSS/JS + WebAssembly)**, việc deploy lên Vercel cực kỳ đơn giản và hoàn toàn miễn phí:

### Cách 1: Sử dụng Vercel CLI

```bash
# Cài đặt Vercel CLI (nếu chưa có)
npm install -g vercel

# Deploy ngay từ thư mục hiện tại
vercel
```

Làm theo hướng dẫn trên màn hình (chọn Yes cho các thiết lập mặc định).

### Cách 2: Deploy qua GitHub / Vercel Dashboard

1. Đẩy code lên kho lưu trữ GitHub của bạn:
   ```bash
   git init
   git add .
   git commit -m "Kaggriculture Web Arena"
   git branch -M main
   git remote add origin https://github.com/<username>/<repo-name>.git
   git push -u origin main
   ```
2. Truy cập [https://vercel.com/new](https://vercel.com/new).
3. Import GitHub repository vừa tạo.
4. Nhấn **Deploy** (Vercel tự động nhận diện cấu hình trong `vercel.json`).
5. Web App của bạn sẽ được kích hoạt tại `https://<ten-du-an>.vercel.app`!
