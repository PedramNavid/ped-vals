# LLM Content Generation Evaluation App

A web application to systematically evaluate which LLM (OpenAI, Anthropic, Google) and which prompting strategy produces the best marketing content aligned with your personal writing style.

## Features

- **Multi-Provider Support**: Test OpenAI GPT-4, Anthropic Claude, and Google Gemini
- **Dual Prompting Strategies**: Compare structured vs example-based prompting
- **Blind Evaluation**: Unbiased content evaluation with randomized presentation
- **Comprehensive Analysis**: Detailed insights on model performance, costs, and quality metrics
- **Export Capabilities**: Download results as CSV for further analysis

## Setup Instructions

### 1. Clone and Navigate to Project

```bash
cd llm-content-eval
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

Create a `.env` file based on the example:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

### 4. Initialize Database

The database will be automatically initialized when you first run the application. Tasks will be loaded from `data/tasks.json`.

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

Or directly with Python:

```bash
python -m app.main
```

The application will be available at `http://localhost:8000`

## Usage Guide

### 1. Create an Experiment

1. Navigate to `http://localhost:8000`
2. Click "Create New Experiment"
3. Provide:
   - Experiment name and description
   - 2-3 samples of your writing style
   - Select models to test (OpenAI, Anthropic, Google)
   - Choose prompting strategies (Structured, Example-based)
   - Select tasks to generate content for

### 2. Generate Content

1. After creating an experiment, click "Generate"
2. Monitor progress as the app generates content using all selected combinations
3. View generation statistics including cost and latency

### 3. Evaluate Content

1. Once generation is complete, proceed to evaluation
2. Content is presented blindly (without revealing the source model)
3. Score each piece on:
   - Voice/Style Match (1-5)
   - Coherence & Flow (1-5)
   - Engaging/Compelling (1-5)
   - Meets Brief Requirements (1-5)
   - Overall Quality (1-5)
4. Indicate if you would publish (yes/no/with edits)
5. Estimate editing time needed

### 4. Analyze Results

1. View comprehensive analysis including:
   - Summary statistics
   - Best/worst performing combinations
   - Performance by model
   - Performance by strategy
   - Task-specific insights
2. Export results as CSV for further analysis

## Project Structure

```
llm-content-eval/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Database models
│   ├── schemas.py              # Pydantic schemas
│   ├── database.py             # Database configuration
│   ├── llm_clients.py          # LLM API integrations
│   ├── generation_service.py   # Content generation logic
│   ├── evaluation_service.py   # Evaluation logic
│   ├── analysis_service.py     # Analysis logic
│   └── routers/               # API endpoints
├── static/                     # CSS and JavaScript
├── templates/                  # HTML templates
├── data/
│   ├── tasks.json             # Task definitions
│   └── database.db            # SQLite database
├── config.py                  # Configuration
├── requirements.txt           # Dependencies
└── .env                      # API keys (create from .env.example)
```

## API Endpoints

- `GET /` - Dashboard
- `POST /api/experiments` - Create experiment
- `GET /api/experiments` - List experiments
- `POST /api/generations/start` - Start generation
- `GET /api/evaluations/next/{id}` - Get next item to evaluate
- `POST /api/evaluations` - Submit evaluation
- `GET /api/analysis/{id}/summary` - Get analysis summary
- `GET /api/analysis/{id}/export` - Export as CSV

## Troubleshooting

### API Key Issues
- Ensure all API keys are correctly set in `.env`
- Test connections with: `POST /api/generations/test-llm`

### Database Issues
- Delete `data/database.db` and restart to reinitialize
- Tasks are loaded from `data/tasks.json` on startup

### Generation Failures
- Check API rate limits for your providers
- Monitor the generation log for specific errors
- Failed generations can be retried individually

## Cost Considerations

- The app tracks costs for each generation
- Default configuration: ~$0.10-0.50 per full experiment (36 generations)
- Costs vary by model and token usage
- Monitor total costs in the generation progress view

## Development

To modify the application:

1. **Add new models**: Update `config.py` and `llm_clients.py`
2. **Add new tasks**: Edit `data/tasks.json`
3. **Modify evaluation criteria**: Update `schemas.py` and `templates/evaluate.html`
4. **Enhance analysis**: Extend `analysis_service.py`

## License

This project is for evaluation and testing purposes. Ensure compliance with the terms of service for each LLM provider.