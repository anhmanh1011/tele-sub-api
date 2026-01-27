#!/usr/bin/env python3
"""
Script de dang ky webhook URL voi Telegram sau khi deploy len Cloud Functions.

Cach su dung:
    python set_webhook.py <TELEGRAM_TOKEN> <CLOUD_FUNCTION_URL>

Vi du:
    python set_webhook.py "123456:ABC-DEF" "https://asia-southeast1-myproject.cloudfunctions.net/telegram-bot"
"""

import sys
import requests


def set_webhook(token: str, webhook_url: str) -> dict:
    """Dang ky webhook URL voi Telegram Bot API."""
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    response = requests.post(api_url, json={"url": webhook_url})
    return response.json()


def get_webhook_info(token: str) -> dict:
    """Lay thong tin webhook hien tai."""
    api_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    response = requests.get(api_url)
    return response.json()


def delete_webhook(token: str) -> dict:
    """Xoa webhook (chuyen ve polling mode)."""
    api_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    response = requests.post(api_url)
    return response.json()


def main():
    if len(sys.argv) < 2:
        print("Su dung: python set_webhook.py <TELEGRAM_TOKEN> [CLOUD_FUNCTION_URL]")
        print("")
        print("Vi du:")
        print('  python set_webhook.py "123456:ABC" "https://region-project.cloudfunctions.net/telegram-bot"')
        print('  python set_webhook.py "123456:ABC" --info    # Xem thong tin webhook')
        print('  python set_webhook.py "123456:ABC" --delete  # Xoa webhook')
        sys.exit(1)

    token = sys.argv[1]

    if len(sys.argv) == 2 or sys.argv[2] == "--info":
        # Xem thong tin webhook
        print("Dang lay thong tin webhook...")
        result = get_webhook_info(token)
        if result.get("ok"):
            info = result.get("result", {})
            print(f"URL: {info.get('url', '(chua set)')}")
            print(f"Pending updates: {info.get('pending_update_count', 0)}")
            if info.get("last_error_message"):
                print(f"Last error: {info.get('last_error_message')}")
        else:
            print(f"Loi: {result}")
    elif sys.argv[2] == "--delete":
        # Xoa webhook
        print("Dang xoa webhook...")
        result = delete_webhook(token)
        if result.get("ok"):
            print("Da xoa webhook thanh cong. Bot se su dung polling mode.")
        else:
            print(f"Loi: {result}")
    else:
        # Set webhook
        webhook_url = sys.argv[2]
        print(f"Dang dang ky webhook: {webhook_url}")
        result = set_webhook(token, webhook_url)
        if result.get("ok"):
            print("Dang ky webhook thanh cong!")
            print("")
            print("Kiem tra thong tin webhook:")
            info_result = get_webhook_info(token)
            if info_result.get("ok"):
                info = info_result.get("result", {})
                print(f"  URL: {info.get('url')}")
                print(f"  Pending updates: {info.get('pending_update_count', 0)}")
        else:
            print(f"Loi khi dang ky webhook: {result}")


if __name__ == "__main__":
    main()
