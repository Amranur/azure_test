from fastapi import FastAPI
from crud_api import router as crud_router
from auth_api import router as auth_router
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()


app = FastAPI()
SESSION_SECRET_KEY = os.getenv('SESSION_SECRET_KEY')
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of origins to allow
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include the CRUD routes from another file
app.include_router(crud_router)
app.include_router(auth_router)

# Root
@app.get("/")
async def root():
    return {"message": "working"}
