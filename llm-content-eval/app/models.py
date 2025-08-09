from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class ModelProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    GOOGLE = "google"

class ContentType(str, enum.Enum):
    BLOG_INTRO = "blog_intro"
    LINKEDIN = "linkedin"
    ANNOUNCEMENT = "announcement"

class PromptStrategy(str, enum.Enum):
    STRUCTURED = "structured"
    EXAMPLE_BASED = "example_based"

class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    baseline_samples = Column(JSON)  # List of sample texts
    selected_models = Column(JSON)  # List of selected model configs
    selected_strategies = Column(JSON)  # List of selected strategies
    selected_tasks = Column(JSON)  # List of selected task IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="setup")  # setup, generating, evaluating, complete
    
    generations = relationship("Generation", back_populates="experiment")
    evaluations = relationship("Evaluation", back_populates="experiment")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)  # A, B, C, D, E, F
    content_type = Column(SQLEnum(ContentType))
    title = Column(String)
    description = Column(Text)
    structured_prompt = Column(Text)
    example_prompt_template = Column(Text)
    
    generations = relationship("Generation", back_populates="task")

class Generation(Base):
    __tablename__ = "generations"
    
    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    task_id = Column(String, ForeignKey("tasks.id"))
    model_provider = Column(SQLEnum(ModelProvider))
    model_name = Column(String)  # gpt-4, claude-3-opus, gemini-1.5-pro
    prompt_strategy = Column(SQLEnum(PromptStrategy))
    prompt_used = Column(Text)
    generated_content = Column(Text)
    generation_params = Column(JSON)  # temperature, max_tokens, etc
    timestamp = Column(DateTime, default=datetime.utcnow)
    latency_ms = Column(Float)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    cost_usd = Column(Float)
    
    experiment = relationship("Experiment", back_populates="generations")
    task = relationship("Task", back_populates="generations")
    evaluation = relationship("Evaluation", uselist=False, back_populates="generation")

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True)
    generation_id = Column(Integer, ForeignKey("generations.id"))
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    blind_id = Column(String)  # Random ID for blind evaluation
    
    # Scores (1-5 scale)
    voice_match = Column(Integer)
    coherence = Column(Integer)
    engaging = Column(Integer)
    meets_brief = Column(Integer)
    overall_quality = Column(Integer)
    
    # Meta evaluation
    edit_time_minutes = Column(Integer)
    would_publish = Column(String)  # yes, no, with_edits
    notes = Column(Text)
    
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    evaluation_time_seconds = Column(Integer)
    
    generation = relationship("Generation", back_populates="evaluation")
    experiment = relationship("Experiment", back_populates="evaluations")