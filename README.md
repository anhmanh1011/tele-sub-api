# Telegram Bot - Snusbase Email Finder

Bot Telegram để tìm kiếm email từ danh sách domain sử dụng Snusbase API.

## 🚀 Tính năng chính

- **Xử lý song song**: Hỗ trợ nhiều API keys để tăng tốc độ xử lý
- **Theo dõi tiến độ**: Lưu lại tiến độ xử lý và trả về kết quả ngay cả khi bị rate limit
- **Xử lý lỗi thông minh**: Tự động chuyển API key khi gặp lỗi
- **Báo cáo chi tiết**: Tạo file tiến độ với thông tin đầy đủ

## 📁 Cấu trúc file

```
tele-sub-api/
├── snuscheck.py      # Bot Telegram chính
├── snusbase.py       # Module xử lý Snusbase API
├── config.json       # Cấu hình bot và API keys
├── requirements.txt  # Dependencies
└── README.md         # Hướng dẫn sử dụng
```

## ⚙️ Cài đặt

1. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

2. **Cấu hình config.json:**
```json
{
    "TELEGRAM_TOKEN": "YOUR_BOT_TOKEN_HERE",
    "SNUSBASE_API_KEYS": [
        "API_KEY_1",
        "API_KEY_2",
        "API_KEY_3"
    ]
}
```

3. **Chạy bot:**
```bash
python snuscheck.py
```

## 🔧 Cách sử dụng

1. **Khởi động bot:** Gửi lệnh `/start`
2. **Upload file:** Gửi file `domains.txt` chứa danh sách domain (mỗi domain một dòng)
3. **Chờ xử lý:** Bot sẽ xử lý từng batch và hiển thị tiến độ
4. **Nhận kết quả:** Bot sẽ gửi 2 file:
   - `found_*.txt`: Danh sách email tìm thấy
   - `progress_*.txt`: Báo cáo tiến độ xử lý

## 📊 Báo cáo tiến độ

File `progress_*.txt` chứa thông tin chi tiết:

```
=== BÁO CÁO TIẾN ĐỘ XỬ LÝ ===
Thời gian: 2024-01-15 14:30:25
Tổng số domains: 1000
Tổng số batch: 10
Domains đã xử lý thành công: 600
Emails tìm thấy: 150
Batch bị lỗi: 4

=== DOMAINS ĐÃ XỬ LÝ THÀNH CÔNG ===
   1. example1.com
   2. example2.com
   ...

=== BATCH BỊ LỖI ===
Batch 7 (Index 600-699):
  Lỗi: Tất cả API keys đều không hợp lệ hoặc bị rate limit
  Domains: domain1.com, domain2.com, ...
```

## 🚨 Xử lý lỗi

### **Rate Limit (429):**
- Bot tự động chuyển sang API key khác
- Tiếp tục xử lý batch tiếp theo
- Lưu lại thông tin batch bị lỗi

### **API Key không hợp lệ (401):**
- Tự động chuyển sang key khác
- Ghi log chi tiết về key bị lỗi

### **Lỗi kết nối:**
- Thử lại với tất cả API keys
- Tăng thời gian chờ giữa các lần thử

## 💡 Tối ưu hóa

- **Batch size:** Tự động điều chỉnh dựa trên số lượng API keys
- **Thread safety:** Sử dụng lock để đồng bộ hóa việc ghi file
- **Logging:** Ghi log chi tiết cho mỗi thread và API key

## 🔍 Troubleshooting

### **Bot không phản hồi:**
- Kiểm tra `TELEGRAM_TOKEN` trong `config.json`
- Đảm bảo bot đang chạy và không bị block

### **API errors:**
- Kiểm tra `SNUSBASE_API_KEYS` trong `config.json`
- Đảm bảo API keys còn hiệu lực và không bị rate limit

### **File không được gửi:**
- Kiểm tra quyền ghi vào thư mục `/tmp/`
- Đảm bảo có đủ dung lượng ổ đĩa

## 📝 Logs

Bot tạo 2 file log:
- `app.log`: Log chính của bot
- `api.log`: Log chi tiết về API calls

## 🤝 Đóng góp

Nếu bạn muốn đóng góp, hãy:
1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết. 