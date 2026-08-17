# GraphOne AI Intelligence Engine

GraphOne is an AI/venture intelligence ingestion pipeline that collects, normalizes, enriches and exposes structured information about AI startups, products, research papers, jobs and news signals.

## Verified Dataset

| Dataset | Records |
|---|---:|
| Research Papers | 1,000 |
| Startups | 1,000 |
| Products | 1,000 |
| News Signals | 5 |
| AI Jobs | 5 |
| Entity Mapping Log | 2,000 |
| HuggingFace Matches | 996 |
| GitHub Repositories | 23 |
| GitHub Stars | 1,385 |

## Key Features

- arXiv research paper ingestion
- HuggingFace enrichment
- GitHub repository discovery
- GitHub star tracking
- Startup dataset ingestion
- Product dataset ingestion
- AI news signal ingestion
- AI job signal ingestion
- Deterministic entity resolution
- Entity mapping audit log
- SQLite persistence
- Async HTTP ingestion
- FastAPI REST API
- LLM-based extraction orchestration
- Gemini Flash -> Groq Llama -> DeepSeek fallback
- 413 payload handling
- 429 exponential backoff with jitter
- Intelligent text chunking
- Anti-bot/source fallback strategy

## Architecture

Data Sources
    |
    v
Async Ingestion
    |
    v
Normalization
    |
    v
Entity Resolution
    |
    +-------------------+
    |                   |
    v                   v
Enrichment        LLM Extraction
    |                   |
    |          Gemini -> Groq -> DeepSeek
    |
    +--------+----------+
             |
             v
           SQLite
             |
             v
         FastAPI API
             |
             v
        Submission XLSX

## API

Base URL:

http://127.0.0.1:8000

### Dataset Counts

GET /datasets

Returns counts for papers, startups, products, news and jobs.

### Statistics

GET /stats

Returns enrichment statistics including total papers, HuggingFace matches, GitHub repositories and GitHub stars.

### Paper Details

GET /papers/{paper_id}

Example:

GET /papers/847

## Installation

Create virtual environment:

python -m venv .venv

Activate:

.\.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

## Run API

uvicorn src.api.main:app --reload

## Verify API

Invoke-RestMethod "http://127.0.0.1:8000/datasets"

Invoke-RestMethod "http://127.0.0.1:8000/stats"

## Technology Stack

- Python
- FastAPI
- SQLite
- Pandas
- AsyncIO
- aiohttp
- arXiv
- HuggingFace
- GitHub API
- Gemini
- Groq
- DeepSeek

## Project Structure

graphone-ai-engine/
|
+-- data/
|   +-- research_papers.db
|   +-- startups.db
|   +-- products.db
|   +-- signals.db
|   +-- entity_mapping_log.csv
|   +-- GraphOne_submission.xlsx
|
+-- src/
|   +-- api/
|   +-- enrichment/
|   +-- entity_resolution/
|   +-- llm/
|
+-- tests/
|
+-- requirements.txt
+-- README.md
+-- .gitignore

## Project Status

Core ingestion, normalization, enrichment, entity resolution, database storage, LLM orchestration and API layers are implemented and verified.

Final verified dataset:

- 1,000 research papers
- 1,000 startups
- 1,000 products
- 5 news signals
- 5 AI jobs
- 2,000 entity mapping records
- 996 HuggingFace matches
- 23 GitHub repositories
- 1,385 GitHub stars

## License

This project is intended for research, evaluation and AI intelligence pipeline development.
