import json
import os
from datetime import datetime, timedelta

TOKEN_FILE = "token.json"

def save_token(token_data):
    """
    Saves the access token and calculates its expiry time.
    """
    # Clover tokens typically expire in 1 hour (3600 seconds)
    expires_in = token_data.get("expires_in", 3600)
    token_data['expires_at'] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
        
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=4)
    print(f"Token saved to {TOKEN_FILE} with expiry at {token_data['expires_at']}")

def load_token():
    """
    Loads the access token from the file. This version is more defensive.
    It reads the file content first before attempting to parse it.
    Returns None if the file doesn't exist or is empty/invalid.
    """
    if not os.path.exists(TOKEN_FILE):
        return None

    try:
        with open(TOKEN_FILE, 'r') as f:
            content = f.read()
            # If the file is empty, content will be an empty string
            if not content:
                return None
            # Only parse if content is not empty
            return json.loads(content)
    except json.JSONDecodeError as e:
        # This catches malformed JSON
        print(f"Warning: Could not decode JSON from {TOKEN_FILE}: {e}")
        return None
    except Exception as e:
        print(f"Error reading token file: {e}")
        return None

def is_token_expired():
    """
    Checks if the stored token is expired.
    """
    token = load_token()
    if not token or 'expires_at' not in token:
        return True
    
    try:
        expires_at = datetime.fromisoformat(token['expires_at'])
        # Add 5 minute buffer before expiry
        return datetime.now() >= (expires_at - timedelta(minutes=5))
    except (ValueError, TypeError) as e:
        print(f"Error parsing token expiry: {e}")
        return True

def get_access_token():
    """
    Returns the access token if it's valid, otherwise None.
    """
    if is_token_expired():
        return None
    token = load_token()
    return token.get("access_token") if token else None

def get_merchant_id():
    """
    Returns the merchant ID from the stored token.
    """
    token = load_token()
    return token.get("merchant_id") if token else None

def clear_token():
    """
    Clears the stored token (useful for logout).
    """
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        print("Token cleared successfully")
