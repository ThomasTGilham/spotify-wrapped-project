import requests
import base64
from urllib.parse import urlencode

# IMPORTANT: Paste your Client ID and Client Secret here
CLIENT_ID = "your client ID here"
CLIENT_SECRET = "your client secret here"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

# Step 1: Get the Authorization URL
auth_headers = {
    "client_id": CLIENT_ID,
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": "user-read-recently-played", # This is the permission we need
}
auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_headers)}"
print(f"\n1. Go to this URL and authorize the app:\n{auth_url}")

# Step 2: Paste the URL you are redirected to
redirected_url = input("\n2. Paste the full URL you were redirected to here: ")
auth_code = redirected_url.split("code=")[1]

# Step 3: Exchange the Authorization Code for an Access Token and Refresh Token
auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
auth_b64 = base64.b64encode(auth_string.encode()).decode()

headers = {
    "Authorization": f"Basic {auth_b64}",
    "Content-Type": "application/x-www-form-urlencoded",
}
data = {
    "grant_type": "authorization_code",
    "code": auth_code,
    "redirect_uri": REDIRECT_URI,
}

result = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
response_json = result.json()

refresh_token = response_json.get("refresh_token")

print(f"\n--- SUCCESS! ---")
print(f"Your Refresh Token is:\n{refresh_token}\n")
print("Save this token. You will add it to Airflow Variables.")
