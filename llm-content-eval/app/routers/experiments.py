from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Experiment, Task
from app.schemas import ExperimentCreate, ExperimentResponse, TaskResponse

router = APIRouter(prefix="/api/experiments", tags=["experiments"])

@router.post("/", response_model=ExperimentResponse)
def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    """Create a new experiment"""
    
    # Validate that tasks exist
    for task_id in experiment.selected_tasks:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=400, detail=f"Task {task_id} not found")
    
    # Create experiment
    db_experiment = Experiment(
        name=experiment.name,
        description=experiment.description,
        baseline_samples=experiment.baseline_samples,
        selected_models=experiment.selected_models,
        selected_strategies=experiment.selected_strategies,
        selected_tasks=experiment.selected_tasks,
        status="setup"
    )
    
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    
    return db_experiment

@router.get("/", response_model=List[ExperimentResponse])
def list_experiments(db: Session = Depends(get_db)):
    """List all experiments"""
    experiments = db.query(Experiment).order_by(Experiment.created_at.desc()).all()
    return experiments

@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """Get experiment details"""
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment

@router.put("/{experiment_id}/status")
def update_experiment_status(experiment_id: int, status: str, db: Session = Depends(get_db)):
    """Update experiment status"""
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    valid_statuses = ["setup", "generating", "evaluating", "complete"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    experiment.status = status
    db.commit()
    
    return {"message": f"Status updated to {status}"}

@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """Delete an experiment and all related data"""
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    db.delete(experiment)
    db.commit()
    
    return {"message": "Experiment deleted successfully"}

@router.get("/tasks/all", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """List all available tasks"""
    tasks = db.query(Task).all()
    return tasks