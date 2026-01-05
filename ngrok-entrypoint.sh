#!/bin/sh
set -e

echo "Waiting for ngrok..."

# Wait until ngrok is ready and returns a public_url
until curl -s http://ngrok:4040/api/tunnels | grep -q "public_url"; do
    sleep 1
done

# Extract the actual ngrok public URL
NGROK_URL=$(curl -s http://ngrok:4040/api/tunnels | jq -r '.tunnels[0].public_url')

echo "Using NGROK_URL=$NGROK_URL"

# Set the webhook directly using curl
echo "Setting webhook..."
WEBHOOK_URL="$NGROK_URL/bot/webhook"

curl -F "url=$WEBHOOK_URL" \
     -F "secret_token=$WEBHOOK_SECRET_KEY" \
     "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook"

echo "\nWebhook set successfully!"
