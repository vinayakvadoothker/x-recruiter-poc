#!/usr/bin/env python3
"""
Automatic X API token refresh script.

This script checks if tokens are valid and automatically refreshes them.
If refresh fails, it guides you through getting new tokens.
"""

import os
import sys
import asyncio
import httpx
import base64
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

async def check_and_refresh_tokens():
    """Check if tokens are valid and refresh if needed."""
    client_id = os.getenv("X_CLIENT_ID")
    client_secret = os.getenv("X_CLIENT_SECRET")
    refresh_token = os.getenv("X_OAUTH2_REFRESH_TOKEN")
    access_token = os.getenv("X_OAUTH2_ACCESS_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        print("❌ Missing required environment variables:")
        missing = []
        if not client_id:
            missing.append("X_CLIENT_ID")
        if not client_secret:
            missing.append("X_CLIENT_SECRET")
        if not refresh_token:
            missing.append("X_OAUTH2_REFRESH_TOKEN")
        print(f"   {', '.join(missing)}")
        print("\n💡 Run 'python scripts/get_x_oauth2_token.py' to get initial tokens.")
        return False
    
    print("🔄 Attempting to refresh OAuth 2.0 tokens...")
    
    try:
        # Try to refresh the token
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        url = "https://api.x.com/2/oauth2/token"
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                new_access_token = result.get("access_token")
                new_refresh_token = result.get("refresh_token")
                
                if new_access_token:
                    print("✅ Successfully refreshed tokens!")
                    print("\n📋 Update your .env file with these new tokens:")
                    print("=" * 60)
                    print(f"X_OAUTH2_ACCESS_TOKEN={new_access_token}")
                    if new_refresh_token:
                        print(f"X_OAUTH2_REFRESH_TOKEN={new_refresh_token}")
                    print("=" * 60)
                    print("\n💡 Note: Restart your backend server after updating .env")
                    return True
                else:
                    print("❌ Refresh response did not contain access_token")
                    return False
            else:
                error_body = response.text
                print(f"❌ Token refresh failed with status {response.status_code}")
                print(f"   Error: {error_body}")
                
                # Check if refresh token is invalid
                if response.status_code == 400:
                    try:
                        error_json = response.json()
                        if "invalid" in error_json.get("error_description", "").lower():
                            print("\n⚠️  Refresh token is invalid or expired.")
                            print("   You need to get new tokens via OAuth flow.")
                            return False
                    except:
                        pass
                
                return False
                
    except Exception as e:
        print(f"❌ Error refreshing tokens: {e}")
        return False


def main():
    """Main function."""
    print("🔐 X API Token Auto-Refresh")
    print("=" * 60)
    print()
    
    # Try to refresh tokens
    success = asyncio.run(check_and_refresh_tokens())
    
    if not success:
        print("\n" + "=" * 60)
        print("🔄 Refresh failed. You need to get new tokens.")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("1. Run: python scripts/get_x_oauth2_token.py")
        print("2. Follow the OAuth flow to get new tokens")
        print("3. Update your .env file with the new tokens")
        print("4. Restart your backend server")
        print()
        sys.exit(1)
    else:
        print("\n✅ Token refresh complete!")
        sys.exit(0)


if __name__ == "__main__":
    main()

