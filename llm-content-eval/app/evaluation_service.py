import random
import string
import time
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Evaluation, Generation, Experiment, Task
from app.schemas import BlindItem, EvaluationSubmit

class EvaluationService:
    def __init__(self):
        self.blind_id_cache = {}  # Maps blind_id to generation_id
        
    def generate_blind_id(self) -> str:
        """Generate a random blind ID"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def get_next_blind_item(self, db: Session, experiment_id: int) -> Optional[BlindItem]:
        """Get the next unevaluated generation for blind evaluation"""
        
        # Find generations without evaluations
        unevaluated = db.query(Generation).filter(
            and_(
                Generation.experiment_id == experiment_id,
                ~Generation.evaluation.has()  # No evaluation exists
            )
        ).all()
        
        if not unevaluated:
            return None
        
        # Pick a random unevaluated generation
        generation = random.choice(unevaluated)
        
        # Generate blind ID
        blind_id = self.generate_blind_id()
        self.blind_id_cache[blind_id] = generation.id
        
        # Get task details
        task = db.query(Task).filter(Task.id == generation.task_id).first()
        
        return BlindItem(
            blind_id=blind_id,
            content=generation.generated_content,
            task_title=task.title,
            task_description=task.description,
            content_type=task.content_type.value
        )
    
    def submit_evaluation(self, db: Session, evaluation_data: EvaluationSubmit, 
                         evaluation_time_seconds: int = None) -> Evaluation:
        """Submit an evaluation for a blind item"""
        
        # Get generation ID from blind ID
        generation_id = self.blind_id_cache.get(evaluation_data.blind_id)
        if not generation_id:
            # Try to find existing evaluation with this blind_id
            existing = db.query(Evaluation).filter(
                Evaluation.blind_id == evaluation_data.blind_id
            ).first()
            if existing:
                raise ValueError(f"Evaluation already exists for blind_id {evaluation_data.blind_id}")
            else:
                raise ValueError(f"Invalid blind_id: {evaluation_data.blind_id}")
        
        # Get generation
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            raise ValueError(f"Generation {generation_id} not found")
        
        # Check if evaluation already exists
        existing_eval = db.query(Evaluation).filter(
            Evaluation.generation_id == generation_id
        ).first()
        if existing_eval:
            raise ValueError(f"Evaluation already exists for generation {generation_id}")
        
        # Create evaluation
        evaluation = Evaluation(
            generation_id=generation_id,
            experiment_id=generation.experiment_id,
            blind_id=evaluation_data.blind_id,
            voice_match=evaluation_data.voice_match,
            coherence=evaluation_data.coherence,
            engaging=evaluation_data.engaging,
            meets_brief=evaluation_data.meets_brief,
            overall_quality=evaluation_data.overall_quality,
            edit_time_minutes=evaluation_data.edit_time_minutes,
            would_publish=evaluation_data.would_publish,
            notes=evaluation_data.notes,
            evaluation_time_seconds=evaluation_time_seconds
        )
        
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        # Remove from cache
        del self.blind_id_cache[evaluation_data.blind_id]
        
        # Check if all evaluations are complete
        self._check_experiment_completion(db, generation.experiment_id)
        
        return evaluation
    
    def get_evaluation_progress(self, db: Session, experiment_id: int) -> Dict:
        """Get evaluation progress for an experiment"""
        
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            return {"error": "Experiment not found"}
        
        total_generations = db.query(Generation).filter(
            Generation.experiment_id == experiment_id
        ).count()
        
        completed_evaluations = db.query(Evaluation).filter(
            Evaluation.experiment_id == experiment_id
        ).count()
        
        return {
            "experiment_id": experiment_id,
            "status": experiment.status,
            "total": total_generations,
            "completed": completed_evaluations,
            "remaining": total_generations - completed_evaluations,
            "percentage": round((completed_evaluations / total_generations) * 100, 1) if total_generations > 0 else 0
        }
    
    def skip_blind_item(self, blind_id: str) -> bool:
        """Skip a blind item (remove from cache)"""
        if blind_id in self.blind_id_cache:
            del self.blind_id_cache[blind_id]
            return True
        return False
    
    def get_all_evaluations(self, db: Session, experiment_id: int) -> List[Evaluation]:
        """Get all evaluations for an experiment"""
        return db.query(Evaluation).filter(
            Evaluation.experiment_id == experiment_id
        ).all()
    
    def _check_experiment_completion(self, db: Session, experiment_id: int):
        """Check if all generations have been evaluated and update experiment status"""
        
        total_generations = db.query(Generation).filter(
            Generation.experiment_id == experiment_id
        ).count()
        
        total_evaluations = db.query(Evaluation).filter(
            Evaluation.experiment_id == experiment_id
        ).count()
        
        if total_generations > 0 and total_generations == total_evaluations:
            experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
            if experiment:
                experiment.status = "complete"
                db.commit()
    
    def reveal_generation_details(self, db: Session, blind_id: str) -> Dict:
        """Reveal the details of a generation after evaluation"""
        
        evaluation = db.query(Evaluation).filter(
            Evaluation.blind_id == blind_id
        ).first()
        
        if not evaluation:
            return {"error": "Evaluation not found"}
        
        generation = evaluation.generation
        task = generation.task
        
        return {
            "blind_id": blind_id,
            "model_provider": generation.model_provider.value,
            "model_name": generation.model_name,
            "prompt_strategy": generation.prompt_strategy.value,
            "task_title": task.title,
            "content_type": task.content_type.value,
            "cost_usd": generation.cost_usd,
            "latency_ms": generation.latency_ms,
            "scores": {
                "voice_match": evaluation.voice_match,
                "coherence": evaluation.coherence,
                "engaging": evaluation.engaging,
                "meets_brief": evaluation.meets_brief,
                "overall_quality": evaluation.overall_quality
            },
            "would_publish": evaluation.would_publish,
            "edit_time_minutes": evaluation.edit_time_minutes
        }