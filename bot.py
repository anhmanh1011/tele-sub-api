import os
import json
import telebot
from telebot.types import Message, InputFile
from snusbase import search_domains
import logging
from datetime import datetime

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
    written_emails = set()
    try:
        with open(result_file, "a", encoding="utf-8") as f_result:
            for i in range(0, len(domains), batch_size):
                batch = domains[i:i+batch_size]
                try:
                    data = search_domains(batch)
                    for table, entries in data.get("results", {}).items():
                        for entry in entries:
                            if "email" in entry and entry["email"] not in written_emails:
                                f_result.write(entry["email"] + "\n")
                                written_emails.add(entry["email"])
                except Exception as e:
                    user_id = message.from_user.id if message.from_user else "unknown"
                    logging.error(f"Lỗi khi truy vấn batch {i//batch_size+1} cho user {user_id}: {e}")
                    bot.reply_to(message, f"Lỗi khi truy vấn batch {i//batch_size+1}: {e}")
                    break
    finally:
        with open(result_file, "rb") as f:
            bot.send_document(message.chat.id, f, caption="Kết quả email tìm thấy!", reply_to_message_id=message.message_id)
        user_id = message.from_user.id if message.from_user else "unknown"
        logging.info(f"Sent result file to user {user_id}")

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling() 