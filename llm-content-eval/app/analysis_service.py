from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models import Generation, Evaluation, Experiment, Task, ModelProvider, PromptStrategy
from app.schemas import AnalysisSummary, ModelAnalysis, StrategyAnalysis, TaskAnalysis
import csv
import io

class AnalysisService:
    
    def get_summary(self, db: Session, experiment_id: int) -> AnalysisSummary:
        """Get summary statistics for an experiment"""
        
        # Get experiment
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # Count generations and evaluations
        total_generations = db.query(Generation).filter(
            Generation.experiment_id == experiment_id
        ).count()
        
        total_evaluations = db.query(Evaluation).filter(
            Evaluation.experiment_id == experiment_id
        ).count()
        
        # Calculate average scores
        avg_scores = db.query(
            func.avg(Evaluation.voice_match).label("voice_match"),
            func.avg(Evaluation.coherence).label("coherence"),
            func.avg(Evaluation.engaging).label("engaging"),
            func.avg(Evaluation.meets_brief).label("meets_brief"),
            func.avg(Evaluation.overall_quality).label("overall_quality")
        ).filter(Evaluation.experiment_id == experiment_id).first()
        
        # Find best and worst combinations based on overall quality
        best_eval = db.query(Evaluation).filter(
            Evaluation.experiment_id == experiment_id
        ).order_by(Evaluation.overall_quality.desc()).first()
        
        worst_eval = db.query(Evaluation).filter(
            Evaluation.experiment_id == experiment_id
        ).order_by(Evaluation.overall_quality.asc()).first()
        
        # Calculate total cost and average latency
        generation_stats = db.query(
            func.sum(Generation.cost_usd).label("total_cost"),
            func.avg(Generation.latency_ms).label("avg_latency")
        ).filter(Generation.experiment_id == experiment_id).first()
        
        best_combination = {}
        worst_combination = {}
        
        if best_eval:
            best_gen = best_eval.generation
            best_combination = {
                "model_provider": best_gen.model_provider.value,
                "model_name": best_gen.model_name,
                "prompt_strategy": best_gen.prompt_strategy.value,
                "task_id": best_gen.task_id,
                "overall_quality": best_eval.overall_quality
            }
        
        if worst_eval:
            worst_gen = worst_eval.generation
            worst_combination = {
                "model_provider": worst_gen.model_provider.value,
                "model_name": worst_gen.model_name,
                "prompt_strategy": worst_gen.prompt_strategy.value,
                "task_id": worst_gen.task_id,
                "overall_quality": worst_eval.overall_quality
            }
        
        return AnalysisSummary(
            experiment_id=experiment_id,
            total_generations=total_generations,
            total_evaluations=total_evaluations,
            avg_scores={
                "voice_match": round(avg_scores.voice_match, 2) if avg_scores.voice_match else 0,
                "coherence": round(avg_scores.coherence, 2) if avg_scores.coherence else 0,
                "engaging": round(avg_scores.engaging, 2) if avg_scores.engaging else 0,
                "meets_brief": round(avg_scores.meets_brief, 2) if avg_scores.meets_brief else 0,
                "overall_quality": round(avg_scores.overall_quality, 2) if avg_scores.overall_quality else 0
            },
            best_combination=best_combination,
            worst_combination=worst_combination,
            total_cost=round(generation_stats.total_cost, 4) if generation_stats.total_cost else 0,
            avg_latency_ms=round(generation_stats.avg_latency, 2) if generation_stats.avg_latency else 0
        )
    
    def analyze_by_model(self, db: Session, experiment_id: int) -> List[ModelAnalysis]:
        """Analyze results grouped by model"""
        
        # Get all unique model combinations
        model_combinations = db.query(
            Generation.model_provider,
            Generation.model_name
        ).filter(
            Generation.experiment_id == experiment_id
        ).distinct().all()
        
        results = []
        
        for provider, model_name in model_combinations:
            # Get evaluations for this model
            evaluations = db.query(Evaluation).join(Generation).filter(
                and_(
                    Generation.experiment_id == experiment_id,
                    Generation.model_provider == provider,
                    Generation.model_name == model_name
                )
            ).all()
            
            if not evaluations:
                continue
            
            # Calculate average scores
            avg_scores = {
                "voice_match": sum(e.voice_match for e in evaluations) / len(evaluations),
                "coherence": sum(e.coherence for e in evaluations) / len(evaluations),
                "engaging": sum(e.engaging for e in evaluations) / len(evaluations),
                "meets_brief": sum(e.meets_brief for e in evaluations) / len(evaluations),
                "overall_quality": sum(e.overall_quality for e in evaluations) / len(evaluations)
            }
            
            # Calculate would_publish rate
            would_publish_count = sum(1 for e in evaluations if e.would_publish in ["yes", "with_edits"])
            would_publish_rate = would_publish_count / len(evaluations) if evaluations else 0
            
            # Get generation stats
            generation_stats = db.query(
                func.avg(Generation.cost_usd).label("avg_cost"),
                func.avg(Generation.latency_ms).label("avg_latency")
            ).filter(
                and_(
                    Generation.experiment_id == experiment_id,
                    Generation.model_provider == provider,
                    Generation.model_name == model_name
                )
            ).first()
            
            results.append(ModelAnalysis(
                model_provider=provider.value,
                model_name=model_name,
                avg_scores={k: round(v, 2) for k, v in avg_scores.items()},
                evaluation_count=len(evaluations),
                avg_cost=round(generation_stats.avg_cost, 4) if generation_stats.avg_cost else 0,
                avg_latency_ms=round(generation_stats.avg_latency, 2) if generation_stats.avg_latency else 0,
                would_publish_rate=round(would_publish_rate, 2)
            ))
        
        # Sort by overall quality
        results.sort(key=lambda x: x.avg_scores["overall_quality"], reverse=True)
        
        return results
    
    def analyze_by_strategy(self, db: Session, experiment_id: int) -> List[StrategyAnalysis]:
        """Analyze results grouped by prompting strategy"""
        
        results = []
        
        for strategy in [PromptStrategy.STRUCTURED, PromptStrategy.EXAMPLE_BASED]:
            # Get evaluations for this strategy
            evaluations = db.query(Evaluation).join(Generation).filter(
                and_(
                    Generation.experiment_id == experiment_id,
                    Generation.prompt_strategy == strategy
                )
            ).all()
            
            if not evaluations:
                continue
            
            # Calculate average scores
            avg_scores = {
                "voice_match": sum(e.voice_match for e in evaluations) / len(evaluations),
                "coherence": sum(e.coherence for e in evaluations) / len(evaluations),
                "engaging": sum(e.engaging for e in evaluations) / len(evaluations),
                "meets_brief": sum(e.meets_brief for e in evaluations) / len(evaluations),
                "overall_quality": sum(e.overall_quality for e in evaluations) / len(evaluations)
            }
            
            # Calculate would_publish rate
            would_publish_count = sum(1 for e in evaluations if e.would_publish in ["yes", "with_edits"])
            would_publish_rate = would_publish_count / len(evaluations) if evaluations else 0
            
            results.append(StrategyAnalysis(
                strategy=strategy.value,
                avg_scores={k: round(v, 2) for k, v in avg_scores.items()},
                evaluation_count=len(evaluations),
                would_publish_rate=round(would_publish_rate, 2)
            ))
        
        return results
    
    def analyze_by_task(self, db: Session, experiment_id: int) -> List[TaskAnalysis]:
        """Analyze results grouped by task"""
        
        # Get all tasks
        tasks = db.query(Task).all()
        results = []
        
        for task in tasks:
            # Get evaluations for this task
            evaluations = db.query(Evaluation).join(Generation).filter(
                and_(
                    Generation.experiment_id == experiment_id,
                    Generation.task_id == task.id
                )
            ).all()
            
            if not evaluations:
                continue
            
            # Calculate average scores
            avg_scores = {
                "voice_match": sum(e.voice_match for e in evaluations) / len(evaluations),
                "coherence": sum(e.coherence for e in evaluations) / len(evaluations),
                "engaging": sum(e.engaging for e in evaluations) / len(evaluations),
                "meets_brief": sum(e.meets_brief for e in evaluations) / len(evaluations),
                "overall_quality": sum(e.overall_quality for e in evaluations) / len(evaluations)
            }
            
            # Find best model and strategy for this task
            best_eval = max(evaluations, key=lambda e: e.overall_quality)
            best_gen = best_eval.generation
            
            results.append(TaskAnalysis(
                task_id=task.id,
                task_title=task.title,
                content_type=task.content_type.value,
                avg_scores={k: round(v, 2) for k, v in avg_scores.items()},
                best_model=f"{best_gen.model_provider.value}/{best_gen.model_name}",
                best_strategy=best_gen.prompt_strategy.value,
                evaluation_count=len(evaluations)
            ))
        
        return results
    
    def export_to_csv(self, db: Session, experiment_id: int) -> str:
        """Export all evaluation data to CSV format"""
        
        # Get all evaluations with related data
        evaluations = db.query(Evaluation).filter(
            Evaluation.experiment_id == experiment_id
        ).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Evaluation ID",
            "Task ID",
            "Task Title",
            "Content Type",
            "Model Provider",
            "Model Name",
            "Prompt Strategy",
            "Voice Match",
            "Coherence",
            "Engaging",
            "Meets Brief",
            "Overall Quality",
            "Would Publish",
            "Edit Time (min)",
            "Notes",
            "Cost (USD)",
            "Latency (ms)",
            "Evaluated At"
        ])
        
        # Write data rows
        for eval in evaluations:
            gen = eval.generation
            task = gen.task
            
            writer.writerow([
                eval.id,
                task.id,
                task.title,
                task.content_type.value,
                gen.model_provider.value,
                gen.model_name,
                gen.prompt_strategy.value,
                eval.voice_match,
                eval.coherence,
                eval.engaging,
                eval.meets_brief,
                eval.overall_quality,
                eval.would_publish,
                eval.edit_time_minutes,
                eval.notes or "",
                gen.cost_usd,
                gen.latency_ms,
                eval.evaluated_at.isoformat()
            ])
        
        return output.getvalue()
    
    def get_heatmap_data(self, db: Session, experiment_id: int) -> Dict:
        """Get data for heatmap visualization (model vs strategy)"""
        
        # Get all unique combinations
        combinations = db.query(
            Generation.model_provider,
            Generation.model_name,
            Generation.prompt_strategy
        ).filter(
            Generation.experiment_id == experiment_id
        ).distinct().all()
        
        heatmap_data = {}
        
        for provider, model_name, strategy in combinations:
            model_key = f"{provider.value}/{model_name}"
            
            if model_key not in heatmap_data:
                heatmap_data[model_key] = {}
            
            # Get average overall quality for this combination
            avg_quality = db.query(
                func.avg(Evaluation.overall_quality)
            ).join(Generation).filter(
                and_(
                    Generation.experiment_id == experiment_id,
                    Generation.model_provider == provider,
                    Generation.model_name == model_name,
                    Generation.prompt_strategy == strategy
                )
            ).scalar()
            
            heatmap_data[model_key][strategy.value] = round(avg_quality, 2) if avg_quality else 0
        
        return heatmap_data