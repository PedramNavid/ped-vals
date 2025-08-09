from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database import init_db, load_tasks
from app.routers import experiments, generations, evaluations, analysis
from config import APP_TITLE, APP_VERSION, DEBUG_MODE

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing database...")
    init_db()
    print("Loading tasks...")
    load_tasks()
    print("Application started successfully!")
    yield
    # Shutdown
    print("Application shutting down...")

# Create FastAPI app
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    debug=DEBUG_MODE,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(experiments.router)
app.include_router(generations.router)
app.include_router(evaluations.router)
app.include_router(analysis.router)

# Page routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    """Experiment setup page"""
    return templates.TemplateResponse("setup.html", {"request": request})

@app.get("/generate/{experiment_id}", response_class=HTMLResponse)
async def generate_page(request: Request, experiment_id: int):
    """Generation progress page"""
    return templates.TemplateResponse(
        "generate.html", 
        {"request": request, "experiment_id": experiment_id}
    )

@app.get("/evaluate/{experiment_id}", response_class=HTMLResponse)
async def evaluate_page(request: Request, experiment_id: int):
    """Blind evaluation page"""
    return templates.TemplateResponse(
        "evaluate.html",
        {"request": request, "experiment_id": experiment_id}
    )

@app.get("/results/{experiment_id}", response_class=HTMLResponse)
async def results_page(request: Request, experiment_id: int):
    """Results and analysis page"""
    return templates.TemplateResponse(
        "results.html",
        {"request": request, "experiment_id": experiment_id}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": APP_TITLE,
        "version": APP_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG_MODE
    )