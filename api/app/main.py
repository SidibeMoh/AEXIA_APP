from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import organizations, cards, audits, scoring, auth

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="API de la plateforme AEXIA - Gouvernance de l'IA explicable",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
allow_credentials=False,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(organizations.router, prefix="/api/v1", tags=["Organizations"])
app.include_router(cards.router, prefix="/api/v1", tags=["AEXIA Cards"])
app.include_router(audits.router, prefix="/api/v1", tags=["Audits"])
app.include_router(scoring.router, prefix="/api/v1", tags=["Scoring"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentification"])

@app.get("/")
def root():
    return {
        "service": "AEXIA Platform API",
        "version": settings.API_VERSION,
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}