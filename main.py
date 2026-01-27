import os
import json
import telebot
from telebot.types import Message
from snusbase import search_domains
import logging
from datetime import datetime
import time
import functions_framework
from flask import Request

# Cấu hình logging cho ứng dụng
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

# Đọc token từ environment variable hoặc config.json (fallback cho local dev)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
if not TELEGRAM_TOKEN:
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]
    except FileNotFoundError:
        logging.error("Không tìm thấy TELEGRAM_TOKEN env var hoặc config.json")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

logging.info("Bot initialized")


@bot.message_handler(commands=["start"])
def send_welcome(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"
    print(f"[HANDLER] send_welcome triggered for user {user_id}")
    try:
        bot.reply_to(
            message, "Gui file domains.txt de bat dau tra cuu email tren Snusbase."
        )
        print(f"[HANDLER] Reply sent successfully to user {user_id}")
    except Exception as e:
        print(f"[HANDLER] Error sending reply: {e}")
        import traceback
        traceback.print_exc()


@bot.message_handler(content_types=["document"])
def handle_document(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"

    if not message.document:
        logging.warning(f"User {user_id} sent message without document.")
        bot.reply_to(message, "Vui lòng gửi file .txt chứa danh sách domain.")
        return
    if not message.document.file_name or not message.document.file_name.endswith(
        ".txt"
    ):
        logging.warning(
            f"User {user_id} sent file with invalid name: {message.document.file_name}"
        )
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
    with open(file_path, "wb") as new_file:
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
    failed_batches = []  # Lưu danh sách batch bị lỗi
    total_batches = (len(domains) + batch_size - 1) // batch_size
    should_stop = False  # Flag để dừng xử lý

    try:
        with open(result_file, "w", encoding="utf-8") as f_result:
            for i in range(0, len(domains), batch_size):
                if should_stop:
                    logging.info(f"Dừng xử lý do tất cả API keys đều bị lỗi")
                    break

                batch = domains[i : i + batch_size]
                batch_index = i // batch_size + 1
                current_domains = domains[i : i + batch_size]

                try:
                    logging.info(
                        f"Xử lý batch {batch_index}/{total_batches} với {len(current_domains)} domains"
                    )
                    data = search_domains(batch)

                    # Lưu domain đã xử lý thành công
                    processed_domains.extend(current_domains)
                    if data:
                        # Ghi emails vào file kết quả
                        for table, entries in data.get("results", {}).items():
                            for entry in entries:
                                if (
                                    "email" in entry
                                    and entry["email"] not in written_emails
                                ):
                                    f_result.write(entry["email"] + "\n")
                                    written_emails.add(entry["email"])

                        logging.info(
                            f"Batch {batch_index} hoàn thành thành công, tìm thấy {len(written_emails)} emails"
                        )

                except Exception as e:
                    user_id = message.from_user.id if message.from_user else "unknown"
                    logging.error(
                        f"Lỗi khi truy vấn batch {batch_index} cho user {user_id}: {e}"
                    )

                    # Lưu thông tin batch bị lỗi
                    failed_batches.append(
                        {
                            "batch_index": batch_index,
                            "start_index": i,
                            "end_index": min(i + batch_size, len(domains)),
                            "domains": current_domains,
                            "error": str(e),
                        }
                    )

                    # Kiểm tra xem có phải tất cả API keys đều bị lỗi không
                    error_msg = str(e)
                    if (
                        "Tất cả API keys đều không hợp lệ hoặc bị rate limit"
                        in error_msg
                    ):
                        logging.warning(
                            f"Tất cả API keys đều bị lỗi, dừng xử lý tại batch {batch_index}"
                        )
                        bot.reply_to(
                            message,
                            f"DUNG XU LY: Tat ca API keys deu bi loi hoac rate limit tai batch {batch_index}",
                        )
                        should_stop = True
                        break
                    elif "Không thể kết nối với Snusbase API" in error_msg:
                        bot.reply_to(
                            message,
                            f"Loi batch {batch_index}: Da thu tat ca API key nhung khong thanh cong. Vui long kiem tra lai cac key trong config.json",
                        )
                        should_stop = False
                        break
                    elif "401" in error_msg or "429" in error_msg:
                        bot.reply_to(
                            message,
                            f"Loi batch {batch_index}: API key bi loi hoac rate limit, da tu dong chuyen sang key khac",
                        )
                    else:
                        bot.reply_to(message, f"Loi batch {batch_index}: {error_msg}")

                    # Không break để tiếp tục với batch tiếp theo nếu chỉ là lỗi key đơn lẻ
                    continue

                time.sleep(1)

    finally:
        # Tạo file tiến độ với thông tin chi tiết
        with open(progress_file, "w", encoding="utf-8") as f_progress:
            f_progress.write(f"=== BAO CAO TIEN DO XU LY ===\n")
            f_progress.write(
                f"Thoi gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f_progress.write(f"Tong so domains: {len(domains)}\n")
            f_progress.write(f"Tong so batch: {total_batches}\n")
            f_progress.write(f"Domains da xu ly thanh cong: {len(processed_domains)}\n")
            f_progress.write(f"Emails tim thay: {len(written_emails)}\n")
            f_progress.write(f"Batch bi loi: {len(failed_batches)}\n")

            if should_stop:
                f_progress.write(
                    f"Trang thai: DUNG XU LY do tat ca API keys deu bi loi\n"
                )
                if failed_batches:
                    last_failed = failed_batches[-1]
                    f_progress.write(
                        f"Diem dung: Batch {last_failed['batch_index']} (Index {last_failed['start_index']}-{last_failed['end_index']-1})\n"
                    )
            else:
                f_progress.write(f"Trang thai: HOAN THANH toan bo\n")

            f_progress.write("\n")

            if processed_domains:
                f_progress.write("=== DOMAINS DA XU LY THANH CONG ===\n")
                for i, domain in enumerate(processed_domains):
                    f_progress.write(f"{i+1:4d}. {domain}\n")
                f_progress.write("\n")

            if failed_batches:
                f_progress.write("=== BATCH BI LOI ===\n")
                for batch_info in failed_batches:
                    f_progress.write(
                        f"Batch {batch_info['batch_index']} (Index {batch_info['start_index']}-{batch_info['end_index']-1}):\n"
                    )
                    f_progress.write(f"  Loi: {batch_info['error']}\n")
                    f_progress.write(
                        f"  Domains: {', '.join(batch_info['domains'])}\n\n"
                    )

        # Gửi file kết quả emails
        with open(result_file, "rb") as f:
            if should_stop:
                caption = f"DUNG XU LY: Tim thay {len(written_emails)} emails tu {len(processed_domains)} domains"
                if failed_batches:
                    last_failed = failed_batches[-1]
                    caption += f"\nDung tai batch {last_failed['batch_index']} (Index {last_failed['start_index']}-{last_failed['end_index']-1})"
                caption += f"\nXem file progress de biet chi tiet"
            else:
                caption = f"Hoan thanh: Tim thay {len(written_emails)} emails tu {len(processed_domains)} domains"

            bot.send_document(
                message.chat.id,
                f,
                caption=caption,
                reply_to_message_id=message.message_id,
            )

        # Gửi file tiến độ
        with open(progress_file, "rb") as f:
            if should_stop:
                bot.send_document(
                    message.chat.id,
                    f,
                    caption="Bao cao tien do (DA DUNG)",
                    reply_to_message_id=message.message_id,
                )
            else:
                bot.send_document(
                    message.chat.id,
                    f,
                    caption="Bao cao tien do (HOAN THANH)",
                    reply_to_message_id=message.message_id,
                )

        user_id = message.from_user.id if message.from_user else "unknown"
        if should_stop:
            logging.info(
                f"Sent result files to user {user_id}: DUNG XU LY - {len(written_emails)} emails, {len(processed_domains)} domains processed"
            )
        else:
            logging.info(
                f"Sent result files to user {user_id}: HOAN THANH - {len(written_emails)} emails, {len(processed_domains)} domains processed"
            )


@functions_framework.http
def telegram_webhook(request: Request):
    """HTTP Cloud Function entry point for Telegram webhook."""
    print(f"Received request: {request.method}")

    if request.method == "POST":
        try:
            json_data = request.get_json(force=True)
            print(f"Received update: {json.dumps(json_data)[:500]}")

            # Parse message directly from JSON
            if "message" in json_data:
                message_data = json_data["message"]
                message = telebot.types.Message.de_json(message_data)
                print(f"Parsed message from chat {message.chat.id}: {message.text}")

                # Check if it's a /start command
                if message.text and message.text.startswith("/start"):
                    print("Triggering send_welcome handler")
                    send_welcome(message)
                # Check if it's a document
                elif message.document:
                    print("Triggering handle_document handler")
                    handle_document(message)
                else:
                    print(f"Unknown message type: {message.content_type}")

            print("Update processed successfully")

        except Exception as e:
            print(f"Error processing webhook: {e}")
            import traceback
            traceback.print_exc()
            return "Error", 500

    return "OK", 200


# Local development: chạy với polling
if __name__ == "__main__":
    logging.info("Running in local development mode with polling")
    bot.remove_webhook()
    bot.infinity_polling()
