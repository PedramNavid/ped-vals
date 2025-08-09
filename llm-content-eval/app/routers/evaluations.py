from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import time
from app.database import get_db
from app.schemas import BlindItem, EvaluationSubmit, EvaluationResponse
from app.evaluation_service import EvaluationService

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])
evaluation_service = EvaluationService()

@router.get("/next/{experiment_id}", response_model=Optional[BlindItem])
def get_next_blind_item(experiment_id: int, db: Session = Depends(get_db)):
    """Get next blind item to evaluate"""
    item = evaluation_service.get_next_blind_item(db, experiment_id)
    if not item:
        return None
    return item

@router.post("/", response_model=EvaluationResponse)
def submit_evaluation(
    evaluation: EvaluationSubmit,
    evaluation_time_seconds: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Submit evaluation for a blind item"""
    try:
        result = evaluation_service.submit_evaluation(
            db, evaluation, evaluation_time_seconds
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/progress/{experiment_id}")
def get_evaluation_progress(experiment_id: int, db: Session = Depends(get_db)):
    """Get evaluation progress for an experiment"""
    progress = evaluation_service.get_evaluation_progress(db, experiment_id)
    if "error" in progress:
        raise HTTPException(status_code=404, detail=progress["error"])
    return progress

@router.post("/skip/{blind_id}")
def skip_blind_item(blind_id: str):
    """Skip a blind item (remove from cache)"""
    success = evaluation_service.skip_blind_item(blind_id)
    if not success:
        raise HTTPException(status_code=404, detail="Blind item not found")
    return {"message": "Item skipped"}

@router.get("/{experiment_id}", response_model=List[EvaluationResponse])
def get_evaluations(experiment_id: int, db: Session = Depends(get_db)):
    """Get all evaluations for an experiment"""
    evaluations = evaluation_service.get_all_evaluations(db, experiment_id)
    return evaluations

@router.get("/reveal/{blind_id}")
def reveal_generation_details(blind_id: str, db: Session = Depends(get_db)):
    """Reveal the details of a generation after evaluation"""
    details = evaluation_service.reveal_generation_details(db, blind_id)
    if "error" in details:
        raise HTTPException(status_code=404, detail=details["error"])
    return details

@router.delete("/{evaluation_id}")
def delete_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Delete an evaluation"""
    from app.models import Evaluation
    
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    db.delete(evaluation)
    db.commit()
    
    return {"message": "Evaluation deleted successfully"}