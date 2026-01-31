from fastapi.middleware.cors import CORSMiddleware
from config import ORIGINS

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    ORIGINS
]

def add_cors_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins = origins,
        allow_credentials = True,
        allow_methods = ['*'],
        allow_headers = ['*']
    )