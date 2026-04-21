from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Aero-Frost Icing Risk API")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "aero-frost-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.backend.main:app", host="127.0.0.1", port=8000, reload=True)
