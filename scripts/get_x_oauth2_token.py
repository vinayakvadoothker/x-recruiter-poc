#!/usr/bin/env python3
"""
Helper script to obtain OAuth 2.0 access token for X API posting.

This script walks you through the OAuth 2.0 PKCE flow to get an access token
with required scopes: 'tweet.write' (for posting), 'dm.read' and 'dm.write' (for DMs).

Usage:
    python scripts/get_x_oauth2_token.py
"""

import os
import sys
from dotenv import load_dotenv

# Try to import xdk, but provide helpful error if not installed
try:
    from xdk import Client
    from xdk.oauth2_auth import OAuth2PKCEAuth
except ImportError:
    print("❌ Error: xdk package not installed.")
    print("Install it with: pip install xdk")
    sys.exit(1)

load_dotenv()

def main():
    # Get Client ID and Secret from environment
    client_id = os.getenv("X_CLIENT_ID")
    client_secret = os.getenv("X_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ Error: X_CLIENT_ID and X_CLIENT_SECRET must be set in .env file")
        print("\nAdd these to your .env file:")
        print("X_CLIENT_ID=your_client_id")
        print("X_CLIENT_SECRET=your_client_secret")
        sys.exit(1)
    
    # Set up OAuth 2.0 PKCE
    redirect_uri = "http://localhost:8000/callback"  # Can be any URL, just needs to match app settings
    scopes = ["tweet.write", "tweet.read", "users.read", "dm.read", "dm.write", "offline.access"]
    
    print("🔐 X API OAuth 2.0 Token Generator")
    print("=" * 50)
    print()
    
    # Step 1: Create PKCE instance
    auth = OAuth2PKCEAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scopes
    )
    
    # Step 2: Get authorization URL
    auth_url = auth.get_authorization_url()
    print("📋 Step 1: Visit this URL to authorize your app:")
    print()
    print(f"   {auth_url}")
    print()
    print("📋 Step 2: After authorizing, you'll be redirected.")
    print("   Copy the FULL URL from your browser's address bar.")
    print()
    
    # Step 3: Get callback URL from user
    print("📥 Step 3: After authorizing, X will redirect you.")
    print("   The URL in your browser should look like:")
    print("   http://localhost:8000/callback?code=XXXXX&state=XXXXX")
    print("   Copy the ENTIRE URL including everything after the '?'")
    print()
    callback_url = input("📥 Paste the full callback URL here: ").strip()
    
    if not callback_url:
        print("❌ Error: No callback URL provided")
        sys.exit(1)
    
    # Validate that the URL contains a code parameter
    if "code=" not in callback_url:
        print("\n❌ Error: The callback URL doesn't contain an authorization code.")
        print("   Make sure you copied the ENTIRE URL from your browser.")
        print("   It should look like: http://localhost:8000/callback?code=XXXXX&state=XXXXX")
        print("\n   Common issues:")
        print("   - You only copied 'http://localhost:8000' (missing the query parameters)")
        print("   - The browser redirected to a different URL")
        print("   - You need to authorize the app first by visiting the URL in Step 1")
        sys.exit(1)
    
    # Step 4: Exchange code for tokens
    try:
        print("\n⏳ Exchanging authorization code for access token...")
        tokens = auth.fetch_token(authorization_response=callback_url)
        
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        print("\n✅ Success! Here are your tokens:")
        print()
        print("=" * 50)
        print("Add this to your .env file:")
        print("=" * 50)
        print(f"X_OAUTH2_ACCESS_TOKEN={access_token}")
        if refresh_token:
            print(f"X_OAUTH2_REFRESH_TOKEN={refresh_token}")
        print("=" * 50)
        print()
        print("💡 Note: Access tokens expire. Use the refresh token to get new ones.")
        print("   The refresh token is long-lived and can be reused.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. The callback URL matches what you configured in console.x.com")
        print("2. You copied the FULL URL including all parameters")
        sys.exit(1)

if __name__ == "__main__":
    main()

