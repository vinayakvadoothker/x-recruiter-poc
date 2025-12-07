#!/bin/bash
# Test script for posting to X using OAuth 2.0 User Context token

# Replace YOUR_OAUTH2_USER_CONTEXT_TOKEN with your actual token from OAuth 2.0 PKCE flow
TOKEN="${X_OAUTH2_ACCESS_TOKEN:-YOUR_OAUTH2_USER_CONTEXT_TOKEN}"

echo "Testing X API v2 POST /2/tweets endpoint..."
echo ""

curl --request POST \
  --url https://api.x.com/2/tweets \
  --header "Authorization: Bearer ${TOKEN}" \
  --header "Content-Type: application/json" \
  --data '{
  "text": "🚀 Testing X API v2 OAuth 2.0 User Context posting! Comment '\''interested'\'' if you'\''re interested"
}'

echo ""
echo ""
echo "Note: If you get 'OAuth 2.0 Application-Only is forbidden', you need a User Context token."
echo "Run: python scripts/get_x_oauth2_token.py"

