from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import AnalysisSummary, ModelAnalysis, StrategyAnalysis, TaskAnalysis
from app.analysis_service import AnalysisService

router = APIRouter(prefix="/api/analysis", tags=["analysis"])
analysis_service = AnalysisService()

@router.get("/{experiment_id}/summary", response_model=AnalysisSummary)
def get_analysis_summary(experiment_id: int, db: Session = Depends(get_db)):
    """Get summary statistics for an experiment"""
    try:
        summary = analysis_service.get_summary(db, experiment_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{experiment_id}/by-model", response_model=List[ModelAnalysis])
def analyze_by_model(experiment_id: int, db: Session = Depends(get_db)):
    """Get analysis grouped by model"""
    results = analysis_service.analyze_by_model(db, experiment_id)
    return results

@router.get("/{experiment_id}/by-strategy", response_model=List[StrategyAnalysis])
def analyze_by_strategy(experiment_id: int, db: Session = Depends(get_db)):
    """Get analysis grouped by prompting strategy"""
    results = analysis_service.analyze_by_strategy(db, experiment_id)
    return results

@router.get("/{experiment_id}/by-task", response_model=List[TaskAnalysis])
def analyze_by_task(experiment_id: int, db: Session = Depends(get_db)):
    """Get analysis grouped by task"""
    results = analysis_service.analyze_by_task(db, experiment_id)
    return results

@router.get("/{experiment_id}/heatmap")
def get_heatmap_data(experiment_id: int, db: Session = Depends(get_db)):
    """Get heatmap data (model vs strategy)"""
    data = analysis_service.get_heatmap_data(db, experiment_id)
    return data

@router.get("/{experiment_id}/export", response_class=PlainTextResponse)
def export_to_csv(experiment_id: int, db: Session = Depends(get_db)):
    """Export all evaluation data as CSV"""
    csv_data = analysis_service.export_to_csv(db, experiment_id)
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=experiment_{experiment_id}_results.csv"
        }
    )