import uuid
import requests
from fastapi import Depends, APIRouter, Request, HTTPException,status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from oauthlib.oauth2 import WebApplicationClient
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
from datetime import datetime
from authlib.integrations.starlette_client import OAuth
import jwt


router = APIRouter()

load_dotenv()
SESSION_SECRET_KEY = os.getenv('SESSION_SECRET_KEY')
# Add Session Middleware

# Helper to create JWT

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')

# Google API endpoints
GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI')

# Github API endpoints
GITHUB_AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

# Create an OAuth 2.0 client
google_client = WebApplicationClient(GOOGLE_CLIENT_ID)
github_client = WebApplicationClient(GITHUB_CLIENT_ID)



#Token

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire

# JWT secret and algorithms
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Placeholder for user creation or lookup
def get_or_create_user(email: str, first_name: str, last_name: str):
    user = {"id": str(uuid.uuid4()), "email": email, "first_name": first_name, "last_name": last_name}
    return user



#google oauth
@router.get("/auth/google/login")
async def google_login(request: Request):
    state = str(uuid.uuid4())
    request.session["state"] = state

    authorization_url = google_client.prepare_request_uri(
        GOOGLE_AUTHORIZATION_URL,
        redirect_uri=GOOGLE_REDIRECT_URI,
        scope=["profile", "email"],
        state=state,
    )

    return RedirectResponse(authorization_url)

@router.get("/auth/google/callback")
async def google_callback(request: Request):
    code = request.query_params.get('code')
    state = request.query_params.get('state')

    if not code or not state:
        raise HTTPException(status_code=400, detail="Invalid callback request")

    if state != request.session.get("state"):
        raise HTTPException(status_code=400, detail="Invalid state")

    try:
        # Exchange authorization code for an access token
        token_url, headers, body = google_client.prepare_token_request(
            GOOGLE_TOKEN_URL,
            authorization_response=str(request.url),  # Ensure URL is a string
            redirect_url=GOOGLE_REDIRECT_URI,
            code=code
        )
        token_response = requests.post(token_url, headers=headers, data=body, auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET))
        token_response.raise_for_status()
        token_data = google_client.parse_request_body_response(token_response.text)
    
        # Get user info
        userinfo_endpoint, headers, _ = google_client.add_token(GOOGLE_USERINFO_URL)
        userinfo_response = requests.get(userinfo_endpoint, headers=headers)
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()
        print(user_info)
        # Notify WebSocket clients about the login success
        # for ws in websocket_connections:
        #     await ws.send_text(f"User {user_info['email']} logged in successfully")
        
        first_name=user_info.get('given_name', ''), 
        last_name=user_info.get('family_name', ''),
        email=user_info['email'],
        # Create a new user if they don't exist
        user = get_or_create_user(email, first_name,last_name)

        #  Generate a JWT token (use existing_user or new_user)
        access_token, expiry_date = create_access_token(data={"user_id":  user['id']})

        return {"access_token": access_token, "token_type": "bearer","user": user}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Error fetching user info")
    







@router.get("/auth/github/login")
async def github_login(request: Request):
    state = str(uuid.uuid4())
    request.session["state"] = state

    authorization_url = github_client.prepare_request_uri(
        GITHUB_AUTHORIZATION_URL,
        redirect_uri=GITHUB_REDIRECT_URI,
        scope=["user:email"],
        state=state,
    )
    return RedirectResponse(authorization_url)


# GitHub callback route
@router.get("/auth/github/callback")
async def github_callback(request: Request):
    code = request.query_params.get('code')
    state = request.query_params.get('state')

    if not code or not state:
        raise HTTPException(status_code=400, detail="Invalid callback request")

    if state != request.session.get("state"):
        raise HTTPException(status_code=400, detail="Invalid state")

    try:
        # 1. Exchange authorization code for access token
        token_url, headers, body = github_client.prepare_token_request(
            GITHUB_TOKEN_URL,
            authorization_response=str(request.url),
            redirect_url=GITHUB_REDIRECT_URI,
            code=code
        )
        token_response = requests.post(
            token_url, headers=headers, data=body, auth=(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET)
        )
        token_response.raise_for_status()
        token_data = github_client.parse_request_body_response(token_response.text)
        access_token = token_data.get("access_token")

        # Get user info and primary email
        headers = {"Authorization": f"token {access_token}"}
        userinfo_response = requests.get(GITHUB_USERINFO_URL, headers=headers)
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()

        emails_response = requests.get(GITHUB_EMAILS_URL, headers=headers)
        emails_response.raise_for_status()
        emails_data = emails_response.json()
        primary_email = next(
            (email['email'] for email in emails_data if email['primary']), None
        )

        # Check if user exists; create if not
        user = get_or_create_user(primary_email, user_info.get('login', '').split()[0], user_info.get('login', '').split()[-1])
       
        # Generate a JWT token
        access_token, expiry_date = create_access_token(data={"user_id": user['id']})
        return {"access_token": access_token, "token_type": "bearer", "user": user}

    except requests.exceptions.RequestException as e:
        print(f"Error during GitHub authentication: {e}")
        raise HTTPException(status_code=500, detail="Error during GitHub authentication")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
