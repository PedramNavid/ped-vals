import random
import asyncio
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models import Generation, Experiment, Task, ModelProvider, PromptStrategy
from app.llm_clients import LLMClient
from config import MODELS

class GenerationService:
    def __init__(self):
        self.llm_client = LLMClient()
        
    def prepare_prompt(self, task: Task, strategy: PromptStrategy, 
                      baseline_samples: List[str]) -> str:
        """Prepare the prompt based on strategy"""
        if strategy == PromptStrategy.STRUCTURED:
            return task.structured_prompt
        elif strategy == PromptStrategy.EXAMPLE_BASED:
            # Select two random samples for the example-based prompt
            if len(baseline_samples) >= 2:
                samples = random.sample(baseline_samples, 2)
            else:
                # If less than 2 samples, use what we have
                samples = baseline_samples + baseline_samples  # Duplicate if only 1
                
            prompt = task.example_prompt_template
            prompt = prompt.replace("{sample1}", samples[0] if samples else "")
            prompt = prompt.replace("{sample2}", samples[1] if len(samples) > 1 else "")
            return prompt
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    async def generate_single(self, 
                            db: Session,
                            experiment_id: int,
                            task_id: str,
                            provider: str,
                            model: str,
                            strategy: PromptStrategy) -> Generation:
        """Generate a single piece of content"""
        
        # Get experiment and task
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
            
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Prepare prompt
        prompt = self.prepare_prompt(task, strategy, experiment.baseline_samples)
        
        # Get generation parameters
        params = MODELS[provider]["params"]
        
        # Generate content
        content, metadata = self.llm_client.generate(provider, model, prompt, params)
        
        # Create generation record
        generation = Generation(
            experiment_id=experiment_id,
            task_id=task_id,
            model_provider=provider,
            model_name=model,
            prompt_strategy=strategy,
            prompt_used=prompt,
            generated_content=content if content else "",
            generation_params=params,
            latency_ms=metadata.get("latency_ms", 0),
            prompt_tokens=metadata.get("prompt_tokens", 0),
            completion_tokens=metadata.get("completion_tokens", 0),
            cost_usd=metadata.get("cost_usd", 0)
        )
        
        db.add(generation)
        db.commit()
        db.refresh(generation)
        
        return generation
    
    async def generate_all_for_experiment(self, 
                                         db: Session, 
                                         experiment_id: int,
                                         progress_callback=None) -> List[Generation]:
        """Generate all content for an experiment"""
        
        # Get experiment
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # Update status
        experiment.status = "generating"
        db.commit()
        
        generations = []
        total_combinations = (len(experiment.selected_models) * 
                            len(experiment.selected_strategies) * 
                            len(experiment.selected_tasks))
        completed = 0
        
        # Generate all combinations
        for model_config in experiment.selected_models:
            provider = model_config["provider"]
            model = model_config["model"]
            
            for strategy in experiment.selected_strategies:
                for task_id in experiment.selected_tasks:
                    try:
                        # Check if this combination already exists
                        existing = db.query(Generation).filter(
                            Generation.experiment_id == experiment_id,
                            Generation.task_id == task_id,
                            Generation.model_provider == provider,
                            Generation.prompt_strategy == strategy
                        ).first()
                        
                        if existing:
                            generations.append(existing)
                        else:
                            # Generate new content
                            generation = await self.generate_single(
                                db, experiment_id, task_id, 
                                provider, model, PromptStrategy(strategy)
                            )
                            generations.append(generation)
                            
                            # Small delay to avoid rate limits
                            await asyncio.sleep(1)
                        
                        completed += 1
                        if progress_callback:
                            progress_callback(completed, total_combinations)
                            
                    except Exception as e:
                        print(f"Error generating {provider}/{model}/{strategy}/{task_id}: {e}")
                        completed += 1
                        if progress_callback:
                            progress_callback(completed, total_combinations)
        
        # Update experiment status
        experiment.status = "evaluating"
        db.commit()
        
        return generations
    
    def get_generation_progress(self, db: Session, experiment_id: int) -> Dict:
        """Get progress of generations for an experiment"""
        
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            return {"error": "Experiment not found"}
        
        total_expected = (len(experiment.selected_models) * 
                         len(experiment.selected_strategies) * 
                         len(experiment.selected_tasks))
        
        completed = db.query(Generation).filter(
            Generation.experiment_id == experiment_id
        ).count()
        
        failed = db.query(Generation).filter(
            Generation.experiment_id == experiment_id,
            Generation.generated_content == ""
        ).count()
        
        return {
            "experiment_id": experiment_id,
            "status": experiment.status,
            "total": total_expected,
            "completed": completed,
            "failed": failed,
            "in_progress": total_expected - completed if experiment.status == "generating" else 0,
            "percentage": round((completed / total_expected) * 100, 1) if total_expected > 0 else 0
        }