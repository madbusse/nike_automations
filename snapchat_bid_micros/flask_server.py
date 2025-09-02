import os, json, secrets, urllib.parse, time
from flask import Flask, redirect, request, session, url_for
import requests
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("SNAP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SNAP_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SNAP_REDIRECT_URI")  # https://internal-weevil-unique.ngrok-free.app
SCOPE = "snapchat-marketing-api"
AUTH_URL = "https://accounts.snapchat.com/login/oauth2/authorize"
TOKEN_URL = "https://accounts.snapchat.com/login/oauth2/access_token"
TOKENS_PATH = "snap_tokens.json"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", secrets.token_hex(16))

def save_tokens(data):
    with open(TOKENS_PATH, "w") as f:
        json.dump(data, f, indent=2)

def load_tokens():
    if not os.path.exists(TOKENS_PATH):
        return None
    with open(TOKENS_PATH) as f:
        return json.load(f)

@app.route("/")
def home():
    return "Snapchat API local auth. Go to /login"

@app.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "state": state,
    }
    return redirect(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

@app.route("/callback")
def callback():
    state = request.args.get("state")
    code = request.args.get("code")
    if not state or state != session.get("oauth_state"):
        return "State mismatch", 400
    if not code:
        return "Missing code", 400

    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,  # must match
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=30)
    resp.raise_for_status()
    tokens = resp.json()
    tokens["obtained_at"] = int(time.time())
    save_tokens(tokens)
    return "Tokens saved. You can close this tab."

def get_access_token():
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No tokens.json — hit /login first.")
    # Refresh if near expiry
    if int(time.time()) - tokens.get("obtained_at", 0) > (tokens.get("expires_in", 3600) - 60):
        data = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": tokens["refresh_token"],
        }
        r = requests.post(TOKEN_URL, data=data, timeout=30)
        r.raise_for_status()
        new_tokens = r.json()
        new_tokens["refresh_token"] = new_tokens.get("refresh_token", tokens["refresh_token"])
        new_tokens["obtained_at"] = int(time.time())
        save_tokens(new_tokens)
        tokens = new_tokens
    return tokens["access_token"]

if __name__ == "__main__":
    app.run(port=5000, debug=True)
