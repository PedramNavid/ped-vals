from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, Task
from typing import Generator
import json
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/database.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/baseline_samples", exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

def load_tasks(json_path: str = "data/tasks.json"):
    """Load tasks from JSON file into database"""
    db = SessionLocal()
    
    try:
        # Check if tasks already exist
        existing_tasks = db.query(Task).count()
        if existing_tasks > 0:
            print(f"Tasks already loaded ({existing_tasks} tasks found)")
            return
        
        # Load tasks from JSON
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Create Task objects
        for task_data in data['tasks']:
            task = Task(
                id=task_data['id'],
                content_type=task_data['content_type'],
                title=task_data['title'],
                description=task_data['description'],
                structured_prompt=task_data['structured_prompt'],
                example_prompt_template=task_data['example_prompt_template']
            )
            db.add(task)
        
        db.commit()
        print(f"Successfully loaded {len(data['tasks'])} tasks")
        
    except FileNotFoundError:
        print(f"Tasks file not found at {json_path}")
    except Exception as e:
        print(f"Error loading tasks: {e}")
        db.rollback()
    finally:
        db.close()

def reset_db():
    """Drop all tables and recreate them"""
    Base.metadata.drop_all(bind=engine)
    init_db()
    print("Database reset successfully")