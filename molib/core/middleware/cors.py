"""CORS 白名单中间件"""
import os
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:28000,http://localhost:8000").split(",") if o.strip()
]


def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
