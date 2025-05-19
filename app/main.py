from fastapi import FastAPI
from app.routers import vakeel_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Vakeel LLM")

# ✅ Mount static frontend folder
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# ✅ Include backend routes
app.include_router(vakeel_router.router, prefix="/api", tags=["Vakeel LLM"])

# ✅ Serve index.html at root
@app.get("/", include_in_schema=False)
def root():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not found"}
