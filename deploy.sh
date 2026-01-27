#!/bin/bash

# Deploy Telegram Bot to Google Cloud Functions Gen 2
#
# Truoc khi chay:
# 1. Cai dat gcloud CLI: https://cloud.google.com/sdk/docs/install
# 2. Dang nhap: gcloud auth login
# 3. Chon project: gcloud config set project YOUR_PROJECT_ID
# 4. Cap nhat credentials trong env.yaml

# === CAU HINH ===
FUNCTION_NAME="snusbase-telegram-bot"
REGION="asia-southeast1"  # Chon region gan nhat
RUNTIME="python311"

# === DEPLOY ===
echo "Deploying $FUNCTION_NAME to $REGION..."

gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=$RUNTIME \
  --region=$REGION \
  --source=. \
  --entry-point=telegram_webhook \
  --trigger-http \
  --allow-unauthenticated \
  --env-vars-file=env.yaml \
  --timeout=540s \
  --memory=512MB \
  --min-instances=0 \
  --max-instances=10

# === LAY URL SAU KHI DEPLOY ===
echo ""
echo "=== DEPLOY HOAN TAT ==="
echo "Lay URL cua function:"
gcloud functions describe $FUNCTION_NAME --region=$REGION --gen2 --format="value(serviceConfig.uri)"
echo ""
echo "Tiep theo: Chay 'python set_webhook.py' de dang ky webhook voi Telegram"
