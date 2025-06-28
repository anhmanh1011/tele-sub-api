# Telegram Bot - Snusbase Email Finder

Bot Telegram để tìm kiếm email từ danh sách domain sử dụng Snusbase API với khả năng tự động chuyển đổi giữa nhiều API key.

## Tính năng

- ✅ Hỗ trợ nhiều Snusbase API key
- ✅ Tự động chuyển sang key khác khi key hiện tại bị lỗi
- ✅ Xử lý rate limit và timeout
- ✅ Logging chi tiết cho việc debug
- ✅ Xử lý batch để tối ưu hiệu suất

## Cài đặt

1. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

2. Cấu hình file `config.json`:
```json
{
    "TELEGRAM_TOKEN": "YOUR_TELEGRAM_BOT_TOKEN_HERE",
    "SNUSBASE_API_KEYS": [
        "YOUR_FIRST_SNUSBASE_API_KEY_HERE",
        "YOUR_SECOND_SNUSBASE_API_KEY_HERE",
        "YOUR_THIRD_SNUSBASE_API_KEY_HERE"
    ]
}
```

## Cách sử dụng

1. Khởi động bot:
```bash
python bot.py
```

2. Trong Telegram, gửi lệnh `/start` để bắt đầu

3. Gửi file `domains.txt` chứa danh sách domain (mỗi domain một dòng)

4. Bot sẽ tự động:
   - Tải file lên
   - Chia thành các batch nhỏ (100 domain/batch)
   - Tìm kiếm email trên Snusbase
   - Tự động chuyển key nếu gặp lỗi
   - Gửi lại file kết quả chứa các email tìm thấy

## Xử lý lỗi API Key

Bot sẽ tự động xử lý các trường hợp sau:

- **401 Unauthorized**: Key không hợp lệ → chuyển sang key khác
- **429 Rate Limit**: Key bị giới hạn tần suất → chuyển sang key khác  
- **Timeout**: Kết nối quá thời gian → thử lại với key khác
- **Lỗi khác**: Thử lại tối đa 3 lần với tất cả key

## Logging

- `app.log`: Log chính của bot
- `api.log`: Log chi tiết của các API call

## Cấu hình nâng cao

Bạn có thể điều chỉnh các thông số sau trong code:

- `batch_size`: Số domain xử lý mỗi batch (mặc định: 100)
- `max_retries`: Số lần thử lại tối đa (mặc định: 3)
- `timeout`: Thời gian chờ API response (mặc định: 30 giây) 