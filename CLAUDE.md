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

## Configuration

**Local development:** Use `config.json`
```json
{
    "TELEGRAM_TOKEN": "bot_token",
    "SNUSBASE_API_KEYS": ["key1", "key2"]
}
```

**Cloud Functions:** Use environment variables
- `TELEGRAM_TOKEN` - Telegram bot token
- `SNUSBASE_API_KEYS` - JSON array string: `["key1","key2"]`

## Deployment to Cloud Functions

1. Update credentials in `deploy.sh`
2. Run `bash deploy.sh`
3. Copy the function URL from output
4. Register webhook: `python set_webhook.py <TOKEN> <URL>`
