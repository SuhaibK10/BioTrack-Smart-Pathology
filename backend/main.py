"""
BioTrack AI — FastAPI Backend
Pathology Report Analysis & Longitudinal Health Tracking System
AMU Final Year Project 2025
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes import reports, patients, alerts, dashboard

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 BioTrack AI backend starting...")
    yield
    print("BioTrack AI backend shutting down.")

app = FastAPI(
    title="BioTrack AI",
    description="AI-powered pathology report analysis and longitudinal health tracking",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router,   prefix="/api/reports",   tags=["Reports"])
app.include_router(patients.router,  prefix="/api/patients",  tags=["Patients"])
app.include_router(alerts.router,    prefix="/api/alerts",    tags=["Alerts"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

@app.get("/")
def root():
    return {"status": "ok", "service": "BioTrack AI", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
