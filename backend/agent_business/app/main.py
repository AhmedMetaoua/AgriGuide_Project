from fastapi import FastAPI

from app.routers.business import router as business_router

app = FastAPI(title="AgriAdvisor — Agent Business", version="0.1.0")

app.include_router(business_router)


@app.get("/health")
def health():
    return {"status": "ok", "agent": "business"}
