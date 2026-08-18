<<<<<<< HEAD
# GraphOne AI Intelligence Engine

AI intelligence ingestion pipeline for collecting, normalizing, enriching, resolving, and exposing structured data from AI research papers, startups, products, jobs, and news signals.

## Verified Dataset

| Dataset             | Records |
| ------------------- | ------: |
| Research Papers     |   1,000 |
| Startups            |   1,000 |
| Products            |   1,000 |
| News Signals        |       5 |
| AI Jobs             |       5 |
| Entity Mapping Log  |   2,000 |
| HuggingFace Matches |     996 |
| GitHub Repositories |      23 |
| GitHub Stars        |   1,385 |

> The trial dataset contains the verified records currently available in the repository. News and job records are reported as collected records; the final submission should include the required source coverage and 24-hour freshness validation for the latest run.

## Key Features

* arXiv research paper ingestion
* Papers with Code / research-to-code correlation
* Startup and product dataset ingestion
* AI news signal ingestion
* AI job signal ingestion
* HuggingFace enrichment
* GitHub repository and star enrichment
* Async HTTP ingestion
* SQLite persistence
* Deterministic entity resolution
* Entity mapping audit log
* LLM-based extraction orchestration
* Gemini Flash → Groq Llama → DeepSeek fallback
* 429 exponential backoff with jitter
* 413 payload handling
* Intelligent text chunking
* FastAPI REST API
* Source fallback and compliant handling of JavaScript-heavy/protected sources
* Structured logging and retry handling

## Architecture

```text
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
              +-----------+-----------+
              |                       |
              v                       v
          Enrichment            LLM Extraction
              |                       |
              |              Gemini → Groq → DeepSeek
              |                       |
              +-----------+-----------+
                          |
                          v
                       SQLite
                          |
                          v
                     FastAPI API
                          |
                          v
                Submission Datasets
                  /    |    \\
                 /     |     \\
          Startups Products Research
                           Papers
                    Jobs / News
                           |
                  Entity Mapping Log
```

## LLM Resilience

The extraction layer uses a multi-provider fallback strategy:

```text
Gemini Flash
     |
     | failure / rate limit
     v
Groq Llama
     |
     | failure / rate limit
     v
DeepSeek
```

### 429 Rate Limit Handling

The pipeline handles `429 Too Many Requests` using exponential backoff with jitter. This prevents aggressive retry loops and allows the system to recover from temporary provider rate limits.

### 413 Payload Handling

Large documents are cleaned and divided into manageable chunks before being sent to the LLM extraction layer. This reduces the risk of oversized request payloads while retaining relevant content.

### Source Traceability

LLM extraction is performed only on source-derived content. Each extracted record retains its source URL, and unavailable fields should remain empty/null rather than being inferred or fabricated.

## Entity Resolution

The entity-resolution layer canonicalizes variations of the same organization or product.

Example:

```text
OpenAI
Open AI
OpenAI, Inc.
     |
     v
  OpenAI
```

Both the raw and canonical values are retained in the Entity Mapping Log for auditability.

## API

### Dataset Statistics

```http
GET /datasets
```

Returns dataset counts for research papers, startups, products, news, and jobs.

### Enrichment Statistics

```http
GET /stats
```

Returns enrichment statistics including:

* Total research papers
* HuggingFace matches
* GitHub repositories
* GitHub stars

### Paper Details

```http
GET /papers/{paper_id}
```

Returns details for an individual research paper.

Example:

```http
GET /papers/847
```

## Project Structure

```text
graphone-ai-engine/
│
├── data/
│   ├── research_papers.db
│   ├── startups.db
│   ├── products.db
│   ├── signals.db
│   ├── entity_mapping_log.csv
│   └── GraphOne_submission.xlsx
│
├── src/
│   ├── api/
│   ├── enrichment/
│   ├── entity_resolution/
│   ├── llm/
│   └── ...
│
├── tests/
│
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run API

```bash
uvicorn src.api.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## Verify API

### Dataset counts

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/datasets"
```

### Enrichment statistics

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/stats"
```

## Technology Stack

* Python
* asyncio
* aiohttp
* SQLite
* FastAPI
* Pydantic
* arXiv
* HuggingFace
* GitHub API
* Gemini
* Groq
* DeepSeek

## Submission Output

The required Google Sheets output is organized into six tabs:

1. **Startups** — minimum 1,000 records
2. **Products** — minimum 1,000 records
3. **Research Papers** — minimum 1,000 records with GitHub enrichment where available
4. **Jobs** — fresh jobs from the monitored sources within the required 24-hour window
5. **News** — fresh news signals from the monitored sources within the required 24-hour window
6. **Entity Mapping Log** — raw entity names mapped to canonical names

The repository also contains the engineering artifacts required for the trial, including source code, API components, tests, and architecture documentation.

## Project Status

The core ingestion, normalization, enrichment, entity-resolution, database storage, LLM orchestration, and API layers are implemented and verified against the current trial dataset.

### Final Verified Dataset

* **1,000** research papers
* **1,000** startups
* **1,000** products
* **5** news signals
* **5** AI jobs
* **2,000** entity mapping records
* **996** HuggingFace matches
* **23** GitHub repositories
* **1,385** GitHub stars

## Data Traceability

Every extracted record is designed to retain its originating source information. LLM extraction is used for structuring and normalization rather than generating unsupported facts. Source URLs are preserved so records can be independently verified.

## Freshness and Deduplication

News and job ingestion uses normalized publication timestamps and freshness filtering. For sources with relative or incomplete timestamps, source metadata and parsing heuristics can be used to determine whether an item is new since the previous run. A stable source URL or derived content identity can be used for deduplication so the same item is not repeatedly processed.

## Scalability

The ingestion layer uses asynchronous processing and modular source adapters. The architecture is designed to scale horizontally by increasing crawler and processing workers without changing the core extraction and normalization logic.

For 500,000+ records, the same pipeline can be deployed with distributed workers, shared persistent storage, queue-based processing, centralized rate limiting, and partitioned workloads. Scaling is therefore primarily an infrastructure concern rather than a rewrite of the extraction logic.

## Anti-Bot and JavaScript-Heavy Sources

For JavaScript-rendered or protected sources, the production strategy is to prefer official APIs and permitted public endpoints where available, use asynchronous browser automation such as Playwright where appropriate, respect rate limits, cache responses, and fall back to alternative legitimate sources when access is denied. CAPTCHA or explicit access controls are treated as boundaries rather than bypassed.
=======
﻿# GraphOne AI Intelligence Engine

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
>>>>>>> c4691ed7d15ee6cc885d221e1d51854cf3c5532c
