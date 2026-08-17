# GraphOne AI Intelligence Engine

AI intelligence data pipeline for ingesting, enriching, normalizing and exposing structured data from research papers, startups, products, AI jobs and news signals.

## Current Dataset

| Dataset | Records |
|---|---:|
| Research Papers | 1,000 |
| Startups | 1,000 |
| Products | 1,000 |
| News Signals | 5 |
| AI Jobs | 3 |
| HuggingFace Matches | 996 |
| GitHub Repositories | 23 |
| GitHub Stars | 1,385 |

## Features

- arXiv research paper ingestion
- HuggingFace enrichment
- GitHub repository discovery
- GitHub star tracking
- Startup dataset ingestion
- Product dataset ingestion
- AI news signal ingestion
- AI job signal ingestion
- SQLite data storage
- FastAPI REST API

## API

Base URL:

http://127.0.0.1:8000

### Dataset Counts

GET /datasets

Returns counts for papers, startups, products, news and jobs.

### Statistics

GET /stats

Returns enrichment statistics including total papers, HuggingFace matches, GitHub matches and GitHub stars.

### Paper Details

GET /papers/{paper_id}

Returns details for an individual research paper.

Example:

GET /papers/847

## Project Structure

graphone-ai-engine/
├── data/
│   ├── research_papers.db
│   ├── startups.db
│   ├── products.db
│   └── signals.db
├── src/
│   ├── api/
│   ├── enrichment/
│   └── ...
├── tests/
├── requirements.txt
├── README.md
└── .gitignore

## Installation

Create virtual environment:

python -m venv .venv

Activate:

.\.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

## Run API

uvicorn src.api.main:app --reload

## Verify

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

## Project Status

Core ingestion, enrichment, database storage and API layers are implemented.

Verified dataset:

- 1,000 research papers
- 1,000 startups
- 1,000 products
- 5 news signals
- 3 AI jobs
- 996 HuggingFace matches
- 23 GitHub repositories
- 1,385 GitHub stars

## License

This project is intended for research, evaluation and AI intelligence pipeline development.
