# Medical AI Workflow Observability Demo

This repository is a synthetic ETL demo inspired by a real class of observability problems in medical AI workflow platforms. It does **not** reuse private schemas, code, data, or internal business logic. The entire project is rebuilt from scratch with fake entities and deterministic synthetic events.

## What the Demo Shows

- synthetic event generation for imaging requests, uploads, queueing, and AI processing
- analytical transformations into lifecycle and module-run facts
- monitoring metrics such as queue delay, processing duration, failure rate, and SLA breaches
- PostgreSQL-ready schema assets and local CSV outputs for easy review

## Architecture

1. `src/medical_ai_demo/generator.py` creates raw operational datasets.
2. `src/medical_ai_demo/pipeline.py` derives analytics tables from the raw events.
3. `src/medical_ai_demo/reporting.py` computes human-readable monitoring summaries.
4. `sql/schema/` and `sql/views/` define PostgreSQL-facing warehouse objects.

The default implementation uses only the Python standard library so it can run locally without extra packages. A PostgreSQL loader stub is included for the next build phase.

## Project Layout

- `docs/` design notes
- `sql/schema/` raw and analytics table definitions
- `sql/views/` reporting views
- `src/medical_ai_demo/` generator, ETL, reporting, and loader code
- `data/generated/` pipeline outputs
- `tests/` pipeline correctness checks

## Quick Start

```bash
make demo
make test
```

This generates:

- raw CSV datasets under `data/generated/raw/`
- analytics CSV datasets under `data/generated/analytics/`
- a markdown report at `data/generated/reports/summary.md`

## Demo Outputs

Key generated metrics include:

- request-to-upload-complete latency
- upload-complete-to-processing-start latency
- queue delay before processing starts
- processing duration by AI module
- failure rate by module and disease
- SLA breaches for queue delay and end-to-end runtime

## Local Commands

```bash
make generate
make etl
make report
```

For direct module execution:

```bash
PYTHONPATH=src python3 -m medical_ai_demo.pipeline generate --seed 7 --requests 120
PYTHONPATH=src python3 -m medical_ai_demo.pipeline etl
PYTHONPATH=src python3 -m medical_ai_demo.pipeline report
```

## PostgreSQL Direction

The repository includes PostgreSQL DDL and views. In a later phase, the `postgres_loader.py` module can be expanded to execute bulk loads into a running container started by `docker-compose.yml`.

## Status

This first build establishes the end-to-end demo skeleton:

- deterministic synthetic raw data
- analytical fact and dimension generation
- monitoring report generation
- baseline tests for lifecycle correctness and metric quality
