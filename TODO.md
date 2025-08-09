# LLM Content Generation Evaluation App - Full Specification

## Project Background & Goals

### Overview
We're building a web application to systematically evaluate which LLM (OpenAI, Anthropic, Google) and which prompting strategy produces the best marketing content. The user is a marketer who wants to test different models and prompting approaches to find what generates content most aligned with their personal writing style.

### Core Objectives
1. Test 3 top-tier LLM providers (OpenAI GPT-4, Anthropic Claude, Google Gemini) 
2. Compare 2 prompting strategies (Structured vs Example-based)
3. Evaluate across 3 content types (Blog intros, LinkedIn posts, Company announcements)
4. Support single-person evaluation with blind testing to reduce bias
5. Analyze results to identify best model/prompt combinations for each content type

### Experimental Design
- **Total generations**: 36 (3 models × 2 prompt strategies × 6 tasks)
- **Evaluation method**: Human judgment on style, coherence, and publishability
- **Key innovation**: Using the evaluator's own writing samples as style references

## Technical Specification

### Tech Stack
- **Backend**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML/JavaScript with Tailwind CSS (served by FastAPI)
- **LLM Clients**: Direct API calls using official SDKs
  - `openai` for GPT-4
  - `anthropic` for Claude
  - `google-generativeai` for Gemini
- **Data Visualization**: Chart.js for results analysis
- **Deployment**: Local development server

### Project Structure
```
llm-content-eval/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── models.py               # SQLAlchemy/Pydantic models
│   ├── database.py             # Database connection/setup
│   ├── schemas.py              # Pydantic schemas for API
│   ├── llm_clients.py          # LLM API integrations
│   ├── generation_service.py   # Business logic for generations
│   ├── evaluation_service.py   # Business logic for evaluations
│   ├── analysis_service.py     # Results analysis
│   └── routers/
│       ├── __init__.py
│       ├── experiments.py      # Experiment endpoints
│       ├── generations.py      # Generation endpoints
│       ├── evaluations.py      # Evaluation endpoints
│       └── analysis.py         # Analysis endpoints
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── base.html
│   ├── index.html              # Dashboard
│   ├── setup.html              # Experiment setup
│   ├── generate.html           # Generation progress
│   ├── evaluate.html           # Blind evaluation interface
│   └── results.html            # Results & analysis
├── data/
│   ├── tasks.json              # Task definitions
│   ├── database.db             # SQLite database
│   └── baseline_samples/       # User's writing samples
├── config.py                   # Configuration settings
├── requirements.txt
└── .env                        # API keys
```

## Data Models

### SQLAlchemy Models (models.py)
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
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
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="setup")  # setup, generating, evaluating, complete

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)  # A, B, C, D, E, F
    content_type = Column(Enum(ContentType))
    title = Column(String)
    description = Column(Text)
    structured_prompt = Column(Text)
    example_prompt_template = Column(Text)

class Generation(Base):
    __tablename__ = "generations"
    
    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    task_id = Column(String, ForeignKey("tasks.id"))
    model_provider = Column(Enum(ModelProvider))
    model_name = Column(String)  # gpt-4, claude-3-opus, gemini-1.5-pro
    prompt_strategy = Column(Enum(PromptStrategy))
    prompt_used = Column(Text)
    generated_content = Column(Text)
    generation_params = Column(JSON)  # temperature, max_tokens, etc
    timestamp = Column(DateTime, default=datetime.utcnow)
    latency_ms = Column(Float)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    cost_usd = Column(Float)

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
```

### Pydantic Schemas (schemas.py)
```python
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str]
    baseline_samples: List[str]
    selected_models: List[Dict[str, str]]  # [{"provider": "openai", "model": "gpt-4"}]
    selected_strategies: List[str]
    selected_tasks: List[str]

class GenerationRequest(BaseModel):
    experiment_id: int
    run_all: bool = False
    specific_combination: Optional[Dict] = None

class EvaluationSubmit(BaseModel):
    blind_id: str
    voice_match: int
    coherence: int
    engaging: int
    meets_brief: int
    overall_quality: int
    edit_time_minutes: int
    would_publish: str
    notes: str

class BlindItem(BaseModel):
    blind_id: str
    content: str
    task_title: str
    task_description: str
    content_type: str
```

## Task Definitions

### tasks.json
```json
{
  "tasks": [
    {
      "id": "A",
      "content_type": "blog_intro",
      "title": "B2B Storytelling",
      "description": "Write an intro for a blog post about why B2B companies struggle with authentic storytelling",
      "structured_prompt": "Write a compelling blog post introduction about why B2B companies struggle with authentic storytelling. Requirements:\n- Target audience: B2B marketing leaders and executives\n- Tone: Professional but conversational, thought-provoking\n- Length: 150-200 words\n- Include: A relatable problem statement, a surprising insight or statistic, and a clear thesis\n- Goal: Hook readers to continue reading about storytelling solutions\n- End with: A transition that previews the value they'll get from the full article",
      "example_prompt_template": "Here are two examples of my writing style:\n\n{sample1}\n\n{sample2}\n\nAnalyze the style of these examples, noting:\n- Sentence structure and rhythm\n- Vocabulary and terminology choices\n- How ideas flow and connect\n- Opening and closing techniques\n- Overall voice and personality\n\nNow, write a compelling blog post introduction about why B2B companies struggle with authentic storytelling while matching the style, voice, and approach demonstrated in the examples above. Maintain the same level of sophistication and personality."
    },
    {
      "id": "B",
      "content_type": "blog_intro", 
      "title": "Digital Transformation Costs",
      "description": "Write an intro for a blog post about the hidden costs of delaying digital transformation",
      "structured_prompt": "Write a compelling blog post introduction about the hidden costs of delaying digital transformation. Requirements:\n- Target audience: C-suite executives in traditional industries\n- Tone: Urgent but not alarmist, data-informed\n- Length: 150-200 words\n- Include: A specific example or scenario, mention of competitive pressure, and opportunity cost\n- Goal: Create urgency without fear-mongering\n- End with: A promise of actionable insights in the article",
      "example_prompt_template": "Here are two examples of my writing style:\n\n{sample1}\n\n{sample2}\n\nAnalyze the style of these examples, noting:\n- Sentence structure and rhythm\n- Vocabulary and terminology choices\n- How ideas flow and connect\n- Opening and closing techniques\n- Overall voice and personality\n\nNow, write a compelling blog post introduction about the hidden costs of delaying digital transformation while matching the style, voice, and approach demonstrated in the examples above. Maintain the same level of sophistication and personality."
    },
    {
      "id": "C",
      "content_type": "linkedin",
      "title": "Failure Lesson",
      "description": "Create a LinkedIn post about a lesson learned from a failed project",
      "structured_prompt": "Create a LinkedIn post about a lesson learned from a failed project or initiative. Requirements:\n- Target audience: Professional network, industry peers\n- Tone: Vulnerable but professional, educational\n- Length: 200-250 words\n- Include: Brief context of the failure, specific lesson learned, how you apply it now\n- Structure: Hook opening, story, lesson, call for engagement\n- Goal: Build thought leadership through authenticity\n- End with: A question to encourage comments",
      "example_prompt_template": "Here are two examples of my writing style:\n\n{sample1}\n\n{sample2}\n\nAnalyze the style of these examples, noting:\n- Sentence structure and rhythm\n- Vocabulary and terminology choices\n- How ideas flow and connect\n- Opening and closing techniques\n- Overall voice and personality\n\nNow, create a LinkedIn post about a lesson learned from a failed project or initiative while matching the style, voice, and approach demonstrated in the examples above. Maintain the same level of sophistication and personality."
    },
    {
      "id": "D",
      "content_type": "linkedin",
      "title": "Industry Trend",
      "description": "Create a LinkedIn post about a new industry trend or insight",
      "structured_prompt": "Create a LinkedIn post announcing a new industry trend or insight you've discovered. Requirements:\n- Target audience: Industry professionals and decision-makers\n- Tone: Confident, insightful, accessible\n- Length: 200-250 words\n- Include: The trend/insight, supporting evidence or example, implications for the industry\n- Structure: Bold claim opening, evidence, what this means, action item\n- Goal: Position as thought leader and generate discussion\n- End with: Call-to-action or thought-provoking question",
      "example_prompt_template": "Here are two examples of my writing style:\n\n{sample1}\n\n{sample2}\n\nAnalyze the style of these examples, noting:\n- Sentence structure and rhythm\n- Vocabulary and terminology choices\n- How ideas flow and connect\n- Opening and closing techniques\n- Overall voice and personality\n\nNow, create a LinkedIn post announcing a new industry trend or insight you've discovered while matching the style, voice, and approach demonstrated in the examples above. Maintain the same level of sophistication and personality."
    },
    {
      "id": "E",
      "content_type": "announcement",
      "title": "AI Feature Launch",
      "description": "Write an announcement for a new AI-powered feature launch",
      "structured_prompt": "Write an announcement for a new AI-powered feature or service launch. Requirements:\n- Target audience: Current customers and prospects\n- Tone: Excited but not hyperbolic, benefit-focused\n- Length: 150-200 words\n- Include: The problem it solves, key capabilities, specific use case, availability\n- Structure: Problem/solution opening, key benefits, proof point, next steps\n- Goal: Drive interest and sign-ups/demos\n- Avoid: Technical jargon, overpromising on AI capabilities",
      "example_prompt_template": "Here are two examples of my writing style:\n\n{sample1}\n\n{sample2}\n\nAnalyze the style of these examples, noting:\n- Sentence structure and rhythm\n- Vocabulary and terminology choices\n- How ideas flow and connect\n- Opening and closing techniques\n- Overall voice and personality\n\nNow, write an announcement for a new AI-powered feature or service launch while matching the style, voice, and approach demonstrated in the examples above. Maintain the same level of sophistication and personality."
    },
    {
      "id": "F",
      "content_type": "announcement",
      "title": "Company Milestone",
      "description": "Write an announcement for a company milestone or achievement",
      "structured_prompt": "Write an announcement for a company milestone or achievement. Requirements:\n- Target audience: Customers, investors, employees, and industry watchers\n- Tone: Proud but humble, forward-looking\n- Length: 150-200 words\n- Include: Specific achievement, what made it possible, what it means for stakeholders\n- Structure: Achievement statement, context/journey, credit to team/customers, vision forward\n- Goal: Build credibility and momentum\n- End with: Forward-looking statement about what's next",
      "example_prompt_template": "Here are two examples of my writing style:\n\n{sample1}\n\n{sample2}\n\nAnalyze the style of these examples, noting:\n- Sentence structure and rhythm\n- Vocabulary and terminology choices\n- How ideas flow and connect\n- Opening and closing techniques\n- Overall voice and personality\n\nNow, write an announcement for a company milestone or achievement while matching the style, voice, and approach demonstrated in the examples above. Maintain the same level of sophistication and personality."
    }
  ]
}
```

## API Endpoints

### Experiments
- `POST /api/experiments` - Create new experiment
- `GET /api/experiments` - List all experiments
- `GET /api/experiments/{id}` - Get experiment details
- `PUT /api/experiments/{id}/status` - Update experiment status

### Generations
- `POST /api/generations/start` - Start generation process
- `GET /api/generations/progress/{experiment_id}` - Get generation progress
- `POST /api/generations/single` - Generate single combination
- `GET /api/generations/{experiment_id}` - Get all generations for experiment

### Evaluations
- `GET /api/evaluations/next/{experiment_id}` - Get next blind item to evaluate
- `POST /api/evaluations` - Submit evaluation
- `GET /api/evaluations/progress/{experiment_id}` - Get evaluation progress
- `GET /api/evaluations/{experiment_id}` - Get all evaluations

### Analysis
- `GET /api/analysis/{experiment_id}/summary` - Get summary statistics
- `GET /api/analysis/{experiment_id}/by-model` - Results grouped by model
- `GET /api/analysis/{experiment_id}/by-strategy` - Results grouped by strategy
- `GET /api/analysis/{experiment_id}/by-task` - Results grouped by task
- `GET /api/analysis/{experiment_id}/export` - Export results as CSV

## LLM Client Implementation (llm_clients.py)

```python
import os
from typing import Dict, Tuple
import time
import openai
import anthropic
import google.generativeai as genai
from config import PRICING

class LLMClient:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
    def generate(self, 
                 provider: str, 
                 model: str, 
                 prompt: str, 
                 params: Dict) -> Tuple[str, Dict]:
        """
        Returns: (generated_content, metadata)
        metadata includes: latency_ms, prompt_tokens, completion_tokens, cost_usd
        """
        start_time = time.time()
        
        if provider == "openai":
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=params.get("temperature", 0.7),
                max_tokens=params.get("max_tokens", 500)
            )
            content = response.choices[0].message.content
            metadata = {
                "latency_ms": (time.time() - start_time) * 1000,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "cost_usd": self._calculate_cost(provider, model, 
                                                response.usage.prompt_tokens, 
                                                response.usage.completion_tokens)
            }
            
        elif provider == "anthropic":
            response = self.anthropic_client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=params.get("temperature", 0.7),
                max_tokens=params.get("max_tokens", 500)
            )
            content = response.content[0].text
            metadata = {
                "latency_ms": (time.time() - start_time) * 1000,
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "cost_usd": self._calculate_cost(provider, model,
                                                response.usage.input_tokens,
                                                response.usage.output_tokens)
            }
            
        elif provider == "google":
            model_obj = genai.GenerativeModel(model)
            response = model_obj.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=params.get("temperature", 0.7),
                    max_output_tokens=params.get("max_tokens", 500)
                )
            )
            content = response.text
            # Note: Token counting for Gemini requires additional setup
            metadata = {
                "latency_ms": (time.time() - start_time) * 1000,
                "prompt_tokens": 0,  # Would need token counting
                "completion_tokens": 0,
                "cost_usd": 0  # Calculate based on Gemini pricing
            }
            
        return content, metadata
    
    def _calculate_cost(self, provider, model, prompt_tokens, completion_tokens):
        # Implement cost calculation based on current pricing
        # Store pricing in config.py
        return 0.0  # Placeholder
```

## UI Templates

### Evaluation Interface (evaluate.html)
```html
<!DOCTYPE html>
<html>
<head>
    <title>Blind Evaluation</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <h1 class="text-3xl font-bold mb-8">Blind Content Evaluation</h1>
        
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <div class="mb-4">
                <span class="text-sm text-gray-500">Task:</span>
                <h2 class="text-xl font-semibold" id="task-title"></h2>
                <p class="text-gray-600" id="task-description"></p>
            </div>
            
            <div class="border-t pt-4">
                <h3 class="font-semibold mb-2">Generated Content:</h3>
                <div class="prose max-w-none" id="content"></div>
            </div>
        </div>
        
        <form id="evaluation-form" class="bg-white rounded-lg shadow-md p-6">
            <h3 class="text-lg font-semibold mb-4">Evaluation Scores (1-5 scale)</h3>
            
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Voice/Style Match</label>
                    <select name="voice_match" class="w-full border rounded px-3 py-2">
                        <option value="1">1 - Not at all</option>
                        <option value="2">2 - Slightly</option>
                        <option value="3">3 - Somewhat</option>
                        <option value="4">4 - Mostly</option>
                        <option value="5">5 - Perfect match</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-1">Coherence & Flow</label>
                    <select name="coherence" class="w-full border rounded px-3 py-2">
                        <option value="1">1 - Poor</option>
                        <option value="2">2 - Below average</option>
                        <option value="3">3 - Average</option>
                        <option value="4">4 - Good</option>
                        <option value="5">5 - Excellent</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-1">Engaging/Compelling</label>
                    <select name="engaging" class="w-full border rounded px-3 py-2">
                        <option value="1">1 - Not engaging</option>
                        <option value="2">2 - Slightly engaging</option>
                        <option value="3">3 - Moderately engaging</option>
                        <option value="4">4 - Very engaging</option>
                        <option value="5">5 - Extremely engaging</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-1">Meets Brief Requirements</label>
                    <select name="meets_brief" class="w-full border rounded px-3 py-2">
                        <option value="1">1 - Misses completely</option>
                        <option value="2">2 - Misses key points</option>
                        <option value="3">3 - Partially meets</option>
                        <option value="4">4 - Mostly meets</option>
                        <option value="5">5 - Fully meets</option>
                    </select>
                </div>
            </div>
            
            <div class="mb-4">
                <label class="block text-sm font-medium mb-1">Overall Quality</label>
                <select name="overall_quality" class="w-full border rounded px-3 py-2">
                    <option value="1">1 - Poor</option>
                    <option value="2">2 - Below average</option>
                    <option value="3">3 - Average</option>
                    <option value="4">4 - Good</option>
                    <option value="5">5 - Excellent</option>
                </select>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Estimated Edit Time (minutes)</label>
                    <input type="number" name="edit_time_minutes" min="0" class="w-full border rounded px-3 py-2">
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-1">Would Publish?</label>
                    <select name="would_publish" class="w-full border rounded px-3 py-2">
                        <option value="yes">Yes, as is</option>
                        <option value="with_edits">Yes, with edits</option>
                        <option value="no">No</option>
                    </select>
                </div>
            </div>
            
            <div class="mb-4">
                <label class="block text-sm font-medium mb-1">Notes</label>
                <textarea name="notes" rows="3" class="w-full border rounded px-3 py-2"></textarea>
            </div>
            
            <div class="flex justify-between">
                <button type="button" id="skip-btn" class="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400">
                    Skip for Now
                </button>
                <button type="submit" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                    Submit & Next
                </button>
            </div>
        </form>
        
        <div class="mt-6 text-center text-sm text-gray-500">
            Progress: <span id="progress">0</span> / <span id="total">0</span> evaluated
        </div>
    </div>
</body>
</html>
```

## Configuration (config.py)
```python
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model configurations
MODELS = {
    "openai": {
        "model": "gpt-4-turbo-preview",
        "params": {
            "temperature": 0.7,
            "max_tokens": 500
        }
    },
    "anthropic": {
        "model": "claude-3-opus-20240229",
        "params": {
            "temperature": 0.7,
            "max_tokens": 500
        }
    },
    "google": {
        "model": "gemini-1.5-pro",
        "params": {
            "temperature": 0.7,
            "max_tokens": 500
        }
    }
}

# Pricing per 1K tokens (update with current pricing)
PRICING = {
    "openai": {
        "gpt-4-turbo-preview": {
            "input": 0.01,
            "output": 0.03
        }
    },
    "anthropic": {
        "claude-3-opus-20240229": {
            "input": 0.015,
            "output": 0.075
        }
    },
    "google": {
        "gemini-1.5-pro": {
            "input": 0.00125,
            "output": 0.005
        }
    }
}

# Database
DATABASE_URL = "sqlite:///data/database.db"
```

## Key Implementation Notes

1. **Blind Evaluation System**: 
   - Generate random IDs for each piece of content
   - Present in randomized order
   - Don't reveal source until analysis phase

2. **Generation Order**:
   - Randomize the order of generations to avoid API rate limit clustering
   - Add small delays between API calls if needed
   - Track progress and allow pause/resume

3. **Cost Tracking**:
   - Calculate and display running costs during generation
   - Show cost per model/strategy in analysis

4. **Analysis Features**:
   - Heatmap of scores (model vs strategy)
   - Best/worst performing combinations
   - Statistical significance tests (if you add them later)
   - Export all data to CSV for external analysis

5. **Error Handling**:
   - Retry logic for API failures
   - Save partial progress
   - Clear error messages to user

6. **User Flow**:
   1. Setup: Upload baseline samples, select models/tasks
   2. Generate: Run all 36 generations with progress tracking
   3. Evaluate: Blind evaluation interface
   4. Analyze: View results and identify best performers

## Getting Started Instructions

1. Install dependencies:
```bash
pip install fastapi uvicorn sqlalchemy openai anthropic google-generativeai python-dotenv
```

2. Set up environment variables in `.env`:
```
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here  
GOOGLE_API_KEY=your_key_here
```

3. Initialize database and load tasks:
```bash
python -c "from app.database import init_db; init_db()"
python -c "from app.database import load_tasks; load_tasks('data/tasks.json')"
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

5. Access at `http://localhost:8000`

This specification provides everything needed to build the complete evaluation system. The app will allow systematic testing of different LLMs and prompting strategies, with blind evaluation to ensure unbiased results and comprehensive analysis to identify the best approach for each content type.
