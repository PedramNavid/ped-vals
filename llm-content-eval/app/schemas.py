from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.models import ModelProvider, ContentType, PromptStrategy

class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    baseline_samples: List[str]
    selected_models: List[Dict[str, str]]  # [{"provider": "openai", "model": "gpt-4"}]
    selected_strategies: List[str]
    selected_tasks: List[str]

class ExperimentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    baseline_samples: List[str]
    selected_models: List[Dict[str, str]]
    selected_strategies: List[str]
    selected_tasks: List[str]
    created_at: datetime
    status: str
    
    class Config:
        from_attributes = True

class GenerationRequest(BaseModel):
    experiment_id: int
    run_all: bool = False
    specific_combination: Optional[Dict] = None

class GenerationProgress(BaseModel):
    experiment_id: int
    total: int
    completed: int
    in_progress: int
    failed: int

class EvaluationSubmit(BaseModel):
    blind_id: str
    voice_match: int
    coherence: int
    engaging: int
    meets_brief: int
    overall_quality: int
    edit_time_minutes: int
    would_publish: str
    notes: Optional[str] = ""

class BlindItem(BaseModel):
    blind_id: str
    content: str
    task_title: str
    task_description: str
    content_type: str

class TaskResponse(BaseModel):
    id: str
    content_type: ContentType
    title: str
    description: str
    structured_prompt: str
    example_prompt_template: str
    
    class Config:
        from_attributes = True

class GenerationResponse(BaseModel):
    id: int
    experiment_id: int
    task_id: str
    model_provider: ModelProvider
    model_name: str
    prompt_strategy: PromptStrategy
    generated_content: str
    timestamp: datetime
    latency_ms: float
    cost_usd: float
    
    class Config:
        from_attributes = True

class EvaluationResponse(BaseModel):
    id: int
    generation_id: int
    blind_id: str
    voice_match: int
    coherence: int
    engaging: int
    meets_brief: int
    overall_quality: int
    edit_time_minutes: int
    would_publish: str
    notes: Optional[str]
    evaluated_at: datetime
    
    class Config:
        from_attributes = True

class AnalysisSummary(BaseModel):
    experiment_id: int
    total_generations: int
    total_evaluations: int
    avg_scores: Dict[str, float]
    best_combination: Dict[str, Any]
    worst_combination: Dict[str, Any]
    total_cost: float
    avg_latency_ms: float

class ModelAnalysis(BaseModel):
    model_provider: str
    model_name: str
    avg_scores: Dict[str, float]
    evaluation_count: int
    avg_cost: float
    avg_latency_ms: float
    would_publish_rate: float

class StrategyAnalysis(BaseModel):
    strategy: str
    avg_scores: Dict[str, float]
    evaluation_count: int
    would_publish_rate: float

class TaskAnalysis(BaseModel):
    task_id: str
    task_title: str
    content_type: str
    avg_scores: Dict[str, float]
    best_model: str
    best_strategy: str
    evaluation_count: int