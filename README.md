# Org-YAML-Creator

Scans org telemetry to create semantic YAML files for RAG and Text-to-SQL applications.

## Telemetry-to-YAML scaffold

This repository now includes a modular Python scaffold under `telemetry_to_yaml/`:

- `providers/`:
  - `base.py`: abstract `BaseProvider` contract for metadata + query-log extraction.
  - `postgres.py`: lightweight `PostgresProvider` implementation with env/.env credentials.
- `parser/`:
  - `analyzer.py`: telemetry parser for joins, column access frequency, and candidate aggregations.
- `generator/`:
  - `schemas.py`: strict Pydantic v2 schemas for dbt semantic YAML (`semantic_models`, `dimensions`, `measures`).
  - `yaml_writer.py`: manifest builder + YAML writer.
- `main.py`: CLI pipeline entrypoint.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py --provider postgres --output semantic_models.yml --limit 1000
```

Credentials are loaded from standard environment variables and optionally from `.env`:
`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
