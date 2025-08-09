from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Generation, PromptStrategy
from app.schemas import GenerationRequest, GenerationProgress, GenerationResponse
from app.generation_service import GenerationService
import asyncio

router = APIRouter(prefix="/api/generations", tags=["generations"])
generation_service = GenerationService()

@router.post("/start")
async def start_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start generation process for an experiment"""
    
    if request.run_all:
        # Run all generations in background
        background_tasks.add_task(
            run_all_generations,
            db,
            request.experiment_id
        )
        return {"message": "Generation started in background", "experiment_id": request.experiment_id}
    else:
        # Generate specific combination
        if not request.specific_combination:
            raise HTTPException(status_code=400, detail="specific_combination required when run_all is False")
        
        generation = await generation_service.generate_single(
            db,
            request.experiment_id,
            request.specific_combination["task_id"],
            request.specific_combination["provider"],
            request.specific_combination["model"],
            PromptStrategy(request.specific_combination["strategy"])
        )
        
        return {"message": "Generation completed", "generation_id": generation.id}

async def run_all_generations(db: Session, experiment_id: int):
    """Background task to run all generations"""
    try:
        await generation_service.generate_all_for_experiment(db, experiment_id)
    except Exception as e:
        print(f"Error in background generation: {e}")

@router.get("/progress/{experiment_id}", response_model=GenerationProgress)
def get_generation_progress(experiment_id: int, db: Session = Depends(get_db)):
    """Get generation progress for an experiment"""
    progress = generation_service.get_generation_progress(db, experiment_id)
    if "error" in progress:
        raise HTTPException(status_code=404, detail=progress["error"])
    return progress

@router.post("/single")
async def generate_single(
    experiment_id: int,
    task_id: str,
    provider: str,
    model: str,
    strategy: str,
    db: Session = Depends(get_db)
):
    """Generate a single combination"""
    try:
        generation = await generation_service.generate_single(
            db, experiment_id, task_id, provider, model, PromptStrategy(strategy)
        )
        return GenerationResponse.from_orm(generation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{experiment_id}", response_model=List[GenerationResponse])
def get_generations(experiment_id: int, db: Session = Depends(get_db)):
    """Get all generations for an experiment"""
    generations = db.query(Generation).filter(
        Generation.experiment_id == experiment_id
    ).all()
    return generations

@router.get("/{experiment_id}/{generation_id}", response_model=GenerationResponse)
def get_generation(experiment_id: int, generation_id: int, db: Session = Depends(get_db)):
    """Get a specific generation"""
    generation = db.query(Generation).filter(
        Generation.id == generation_id,
        Generation.experiment_id == experiment_id
    ).first()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    return generation

@router.post("/test-llm")
def test_llm_connections():
    """Test connections to all LLM providers"""
    service = GenerationService()
    results = service.llm_client.test_connection()
    return {
        "connections": results,
        "summary": f"{sum(results.values())}/{len(results)} providers connected"
    }