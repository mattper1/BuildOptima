from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models  # noqa: F401 — registers all ORM models with Base
from db.database import Base, engine
from routers import auth, builds, optimizer

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BuildOptima API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(builds.router)
app.include_router(optimizer.router)


@app.get("/health")
def health():
    return {"status": "ok"}
