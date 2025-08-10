# shoyu
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![Maintainer](https://img.shields.io/badge/maintainer-@louisbrulenaudet-blue)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)
![Package Manager](https://img.shields.io/badge/package%20manager-uv-purple.svg)

## Introduction

**shoyu** is a Python package for privacy-preserving, large-scale analysis and visualization of Hugging Face model statistics. It features advanced asynchronous and synchronous web search via Tor, making it ideal for LLM analytics, automated research, and data science workflows that require both scale and anonymity.

shoyu is designed for:
- **LLM evaluation and benchmarking**: Automate the collection and analysis of model metadata, performance, and resource usage.
- **Automated research**: Integrate privacy-focused web search into data pipelines.
- **Data science workflows**: Enable reproducible, extensible, and robust analytics for NLP and AI research.
- **Privacy-first search**: All queries are routed through multiple Tor circuits with automatic identity rotation.

**Architecture highlights:**
- Async and sync APIs for flexible integration.
- Tor-based search with per-circuit throttling and identity rotation.
- Typed config and result models for safe, extensible analytics.

---

## Features

- **Async & Sync Web Search**: DuckDuckGo search via Tor, with both async and sync APIs.
- **Automatic Identity Rotation**: Per-circuit throttling and identity rotation for privacy and reliability.
- **Batch & Retry Utilities**: Efficient batch search and robust retry mechanisms.
- **Configurable**: Control region, safesearch, time limits, and backend.
- **Extensible Models**: Typed config and result models for integration.
- **LLM Analytics Ready**: Built for large-scale model/statistics analysis.

---

## Implementation Guide

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended for fast, reproducible installs)
- git

### 1. Clone the repository

```bash
git clone https://github.com/louisbrulenaudet/shoyu.git
cd shoyu
```

### 2. Install dependencies using uv

```bash
uv pip install -r requirements.txt
```

Or, for a fully isolated environment:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

> **Note:** `uv` is a drop-in replacement for pip, offering faster and more reproducible installs. See [uv documentation](https://github.com/astral-sh/uv).

### 3. Alternative: Poetry or pip

```bash
poetry install
# or
pip install -r requirements.txt
```

### 4. Development setup

Install dev dependencies and run tests:

```bash
uv pip install -r requirements.txt
uv pip install -r dev-requirements.txt  # if present
pytest
ruff check .
```

---

## Quick Start

### Asynchronous Example

```python
import asyncio
from src.shoyu import AsyncShoyu

async def main():
    async with AsyncShoyu(num_circuits=5, max_queries_per_identity=10) as search:
        for i in range(20):
            try:
                result = await search("orcinus orca description")
                print(f"Result {i + 1}: {result}")
            except Exception as e:
                print(f"Error on query {i + 1}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Synchronous Example

```python
from src.shoyu import Shoyu

with Shoyu(num_circuits=3, max_queries_per_identity=10) as search:
    result = search("orca habitat")
    print(result)
```

### Running the Example Script

```bash
python main.py
```

---

## API Reference

### Main Classes

- **AsyncShoyu**: High-level async search interface (context manager, batch search, load balancing).
- **AsyncWebSearch**: Lower-level async search with Tor integration.
- **Shoyu**: Synchronous high-level interface.
- **WebSearch**: Synchronous lower-level search.

### Models

- **Config**: Configuration options.
- **SearchResult**: Typed search result.

### Enums

- **Backend**: Search backend selection.
- **Region**: Localization.
- **SafeSearch**: Filtering level.
- **TimeLimit**: Time range restriction.
- **ErrorCodes**: Error handling.

---

## Architecture

The following diagram shows the flow of a search request in shoyu:

```mermaid
flowchart TB
    User[User Search Request]
    Shoyu[Shoyu (Async/Synchronous)]
    Tor[Multiple Tor Circuits]
    Search[DuckDuckGo Search]
    Result[Aggregated Results]

    User --> Shoyu
    Shoyu --> Tor
    Tor --> Search
    Search --> Tor
    Tor --> Shoyu
    Shoyu --> Result

    %% Styling
    classDef default fill:#d4b702,stroke:#8b7701,color:#ffffff
    classDef io fill:#4a5568,stroke:#2d3748,color:#ffffff

    class User,Result io
```

---

## Notes

- **uv.lock** is included for reproducible installs with uv.
- All web search traffic is routed through Tor for privacy. Ensure Tor is available on your system.
- For advanced configuration, see `src/shoyu/config.py` and docstrings.

---

## Citing this project

If you use this code in your research, please use the following BibTeX entry.

```BibTeX
@misc{louisbrulenaudet2025,
author = {Louis Brulé Naudet},
title = {shoyu: Privacy-Preserving LLM Analytics and Web Search},
howpublished = {\url{https://github.com/louisbrulenaudet/shoyu}},
year = {2025}
}
```

---

## Feedback

If you have any feedback, please reach out at [louisbrulenaudet@icloud.com](mailto:louisbrulenaudet@icloud.com).
