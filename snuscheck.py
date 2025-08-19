import os
import json
import telebot
from telebot.types import Message, InputFile
from snusbase import search_domains
import logging
from datetime import datetime
import time

# Cấu hình logging cho ứng dụng
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

with open("config.json", "r") as f:
    config = json.load(f)

TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TELEGRAM_TOKEN)

logging.info("Bot started")

@bot.message_handler(commands=['start'])
def send_welcome(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"
    logging.info(f"User {user_id} started bot.")
    bot.reply_to(message, "Gửi file domains.txt để bắt đầu tra cứu email trên Snusbase.")

@bot.message_handler(content_types=['document'])
def handle_document(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"

    if not message.document:
        logging.warning(f"User {user_id} sent message without document.")
        bot.reply_to(message, "Vui lòng gửi file .txt chứa danh sách domain.")
        return
    if not message.document.file_name or not message.document.file_name.endswith('.txt'):
        logging.warning(f"User {user_id} sent file with invalid name: {message.document.file_name}")
        bot.reply_to(message, "Vui lòng gửi file .txt chứa danh sách domain.")
        return
    file_info = bot.get_file(message.document.file_id)
    if not file_info.file_path:
        user_id = message.from_user.id if message.from_user else "unknown"
        logging.error(f"Không thể lấy file từ Telegram cho user {user_id}")
        bot.reply_to(message, "Không thể lấy file từ Telegram. Vui lòng thử lại.")
        return
    file_path = f"/tmp/{message.document.file_name}"
    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)
        bot.reply_to(message, "Dowloaded file successfully")
    user_id = message.from_user.id if message.from_user else "unknown"
    logging.info(f"User {user_id} uploaded file: {file_path}")
    
    # Đọc file và chia batch
    with open(file_path, "r", encoding="utf-8") as f:
        domains = [line.strip() for line in f if line.strip()]
    
    batch_size = 100
    result_filename = f"found_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    result_file = f"/tmp/{result_filename}"
    progress_filename = f"progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    progress_file = f"/tmp/{progress_filename}"
    
    written_emails = set()
    processed_domains = []  # Lưu danh sách domain đã xử lý thành công
    failed_batches = []     # Lưu danh sách batch bị lỗi
    total_batches = (len(domains) + batch_size - 1) // batch_size
    should_stop = False     # Flag để dừng xử lý
    
    try:
        with open(result_file, "w", encoding="utf-8") as f_result:
            for i in range(0, len(domains), batch_size):
                if should_stop:
                    logging.info(f"Dừng xử lý do tất cả API keys đều bị lỗi")
                    break
                    
                batch = domains[i:i+batch_size]
                batch_index = i // batch_size + 1
                current_domains = domains[i:i+batch_size]
                
                try:
                    logging.info(f"Xử lý batch {batch_index}/{total_batches} với {len(current_domains)} domains")
                    data = search_domains(batch)
                    
                    # Lưu domain đã xử lý thành công
                    processed_domains.extend(current_domains)
                    
                    # Ghi emails vào file kết quả
                    for table, entries in data.get("results", {}).items():
                        for entry in entries:
                            if "email" in entry and entry["email"] not in written_emails:
                                f_result.write(entry["email"] + "\n")
                                written_emails.add(entry["email"])
                    
                    logging.info(f"Batch {batch_index} hoàn thành thành công, tìm thấy {len(written_emails)} emails")
                    
                except Exception as e:
                    user_id = message.from_user.id if message.from_user else "unknown"
                    logging.error(f"Lỗi khi truy vấn batch {batch_index} cho user {user_id}: {e}")
                    
                    # Lưu thông tin batch bị lỗi
                    failed_batches.append({
                        'batch_index': batch_index,
                        'start_index': i,
                        'end_index': min(i + batch_size, len(domains)),
                        'domains': current_domains,
                        'error': str(e)
                    })
                    
                    # Kiểm tra xem có phải tất cả API keys đều bị lỗi không
                    error_msg = str(e)
                    if "Tất cả API keys đều không hợp lệ hoặc bị rate limit" in error_msg:
                        logging.warning(f"Tất cả API keys đều bị lỗi, dừng xử lý tại batch {batch_index}")
                        bot.reply_to(message, f"🚨 DỪNG XỬ LÝ: Tất cả API keys đều bị lỗi hoặc rate limit tại batch {batch_index}")
                        should_stop = True
                        break
                    elif "Không thể kết nối với Snusbase API" in error_msg:
                        bot.reply_to(message, f"⚠️ Lỗi batch {batch_index}: Đã thử tất cả API key nhưng không thành công. Vui lòng kiểm tra lại các key trong config.json")
                        should_stop = True
                        break
                    elif "401" in error_msg or "429" in error_msg:
                        bot.reply_to(message, f"⚠️ Lỗi batch {batch_index}: API key bị lỗi hoặc rate limit, đã tự động chuyển sang key khác")
                    else:
                        bot.reply_to(message, f"⚠️ Lỗi batch {batch_index}: {error_msg}")
                    
                    # Không break để tiếp tục với batch tiếp theo nếu chỉ là lỗi key đơn lẻ
                    continue
                
                time.sleep(1)
                
    finally:
        # Tạo file tiến độ với thông tin chi tiết
        with open(progress_file, "w", encoding="utf-8") as f_progress:
            f_progress.write(f"=== BÁO CÁO TIẾN ĐỘ XỬ LÝ ===\n")
            f_progress.write(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f_progress.write(f"Tổng số domains: {len(domains)}\n")
            f_progress.write(f"Tổng số batch: {total_batches}\n")
            f_progress.write(f"Domains đã xử lý thành công: {len(processed_domains)}\n")
            f_progress.write(f"Emails tìm thấy: {len(written_emails)}\n")
            f_progress.write(f"Batch bị lỗi: {len(failed_batches)}\n")
            
            if should_stop:
                f_progress.write(f"Trạng thái: DỪNG XỬ LÝ do tất cả API keys đều bị lỗi\n")
                if failed_batches:
                    last_failed = failed_batches[-1]
                    f_progress.write(f"Điểm dừng: Batch {last_failed['batch_index']} (Index {last_failed['start_index']}-{last_failed['end_index']-1})\n")
            else:
                f_progress.write(f"Trạng thái: HOÀN THÀNH toàn bộ\n")
            
            f_progress.write("\n")
            
            if processed_domains:
                f_progress.write("=== DOMAINS ĐÃ XỬ LÝ THÀNH CÔNG ===\n")
                for i, domain in enumerate(processed_domains):
                    f_progress.write(f"{i+1:4d}. {domain}\n")
                f_progress.write("\n")
            
            if failed_batches:
                f_progress.write("=== BATCH BỊ LỖI ===\n")
                for batch_info in failed_batches:
                    f_progress.write(f"Batch {batch_info['batch_index']} (Index {batch_info['start_index']}-{batch_info['end_index']-1}):\n")
                    f_progress.write(f"  Lỗi: {batch_info['error']}\n")
                    f_progress.write(f"  Domains: {', '.join(batch_info['domains'])}\n\n")
        
        # Gửi file kết quả emails
        with open(result_file, "rb") as f:
            if should_stop:
                caption = f"🛑 DỪNG XỬ LÝ: Tìm thấy {len(written_emails)} emails từ {len(processed_domains)} domains"
                if failed_batches:
                    last_failed = failed_batches[-1]
                    caption += f"\n⚠️ Dừng tại batch {last_failed['batch_index']} (Index {last_failed['start_index']}-{last_failed['end_index']-1})"
                caption += f"\n🔍 Xem file progress để biết chi tiết"
            else:
                caption = f"✅ Hoàn thành: Tìm thấy {len(written_emails)} emails từ {len(processed_domains)} domains"
            
            bot.send_document(message.chat.id, f, caption=caption, reply_to_message_id=message.message_id)
        
        # Gửi file tiến độ
        with open(progress_file, "rb") as f:
            if should_stop:
                bot.send_document(message.chat.id, f, caption="📊 Báo cáo tiến độ (ĐÃ DỪNG)", reply_to_message_id=message.message_id)
            else:
                bot.send_document(message.chat.id, f, caption="📊 Báo cáo tiến độ (HOÀN THÀNH)", reply_to_message_id=message.message_id)
        
        user_id = message.from_user.id if message.from_user else "unknown"
        if should_stop:
            logging.info(f"Sent result files to user {user_id}: DỪNG XỬ LÝ - {len(written_emails)} emails, {len(processed_domains)} domains processed")
        else:
            logging.info(f"Sent result files to user {user_id}: HOÀN THÀNH - {len(written_emails)} emails, {len(processed_domains)} domains processed")

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling() 