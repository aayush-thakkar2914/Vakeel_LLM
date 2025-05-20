from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from app.routers.vakeel_router import router as vakeel_router

app = FastAPI(title="Vakeel LLM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")

app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

app.include_router(vakeel_router, prefix="/api", tags=["vakeel"])

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_path, "index.html"))
