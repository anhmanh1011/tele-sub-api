# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Telegram bot that searches for emails from a list of domains using the Snusbase API. The bot supports multiple API keys with automatic failover and rate limit handling.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Local development (polling mode)
python main.py

# Deploy to Google Cloud Functions
bash deploy.sh

# Set webhook after deployment
python set_webhook.py <TOKEN> <CLOUD_FUNCTION_URL>

# Check webhook status
python set_webhook.py <TOKEN> --info

# View Cloud Function logs
gcloud functions logs read snusbase-telegram-bot --region=asia-southeast1 --gen2 --limit=30
```

## Architecture

**main.py** - Main Telegram bot entry point
- `telegram_webhook(request)` - HTTP handler for Cloud Functions webhook
- Handles `/start` command and document uploads
- Processes uploaded `.txt` files containing domain lists in batches of 100
- Generates two output files: `found_*.txt` (emails) and `progress_*.txt` (processing report)
- Supports both webhook (Cloud Functions) and polling (local dev) modes

**snusbase.py** - Snusbase API client module
- `search_domains(domains, max_retries=3)` - Main function for domain lookups
- Supports multiple API keys with automatic rotation on 401/429 errors
- Implements exponential backoff between retry attempts

**deploy.sh** - Deployment script for Google Cloud Functions Gen 2

**set_webhook.py** - Utility to register/manage Telegram webhook URL

**snuscheck.py** - Legacy polling-based bot (deprecated, use main.py)

## Configuration

**Local development:** Use `config.json`
```json
{
    "TELEGRAM_TOKEN": "bot_token",
    "SNUSBASE_API_KEYS": ["key1", "key2"]
}
```

**Cloud Functions:** Use `env.yaml` (not committed to git)
```yaml
TELEGRAM_TOKEN: "bot_token"
SNUSBASE_API_KEYS: '["key1","key2"]'
```

## Deployment

**GCP Project:** `domain-data-pipeline`
**Region:** `asia-southeast1`
**Function name:** `snusbase-telegram-bot`
**URL:** `https://snusbase-telegram-bot-vhgpl5vnya-as.a.run.app`

Deploy steps:
1. Update credentials in `env.yaml`
2. Run `bash deploy.sh`
3. Register webhook: `python set_webhook.py <TOKEN> <URL>`

## Technical Notes

**pyTelegramBotAPI webhook issue:** `bot.process_new_updates()` does not trigger handlers properly in Cloud Functions. Solution: Parse message directly from JSON and call handlers explicitly (see `telegram_webhook` function in main.py).

**Sensitive files (not in git):**
- `config.json` - Local dev credentials
- `env.yaml` - Cloud Functions credentials
