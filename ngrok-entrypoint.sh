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

# Export it so other commands in this entrypoint can see it
export NGROK_URL

# Execute the command passed to this entrypoint
exec "$@"
