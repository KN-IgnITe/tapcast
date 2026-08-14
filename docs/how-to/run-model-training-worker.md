# Run the Model Training Worker

## Purpose

This guide explains how to build and run the on-demand model training worker.

The worker runs as a long-lived service. It receives training job identifiers
from RabbitMQ, loads job details from PostgreSQL, trains a model and uploads the
resulting model bundle to S3-compatible storage.

For manual training from an existing JSON file, see
[Train and Export Demand Model Manually](train-and-export-demand-model.md).

## Prerequisites

The repository root must contain a configured `.env` file.

The worker requires:

- PostgreSQL,
- RabbitMQ,
- MinIO or another S3-compatible service,
- the `model_training_job` database table,
- sales data for the requested bar.

The expected job structure and RabbitMQ message are described in the
[Model Training Job Contract](../reference/model-training-job-contract.md).

## Build the Worker Image

From the repository root, run:

```bash
docker compose build training
```

The training image contains:

- the training package,
- the shared `ml_common` package,
- `infrastructure/postgres/query_v2.sql`,
- runtime Python dependencies.

## Start the Worker

Start the required services:

```bash
docker compose up -d postgres rabbitmq s3 training
```

Display the current service state:

```bash
docker compose ps
```

Follow the worker logs:

```bash
docker compose logs -f training
```

A successful startup is indicated by:

```text
Waiting for training jobs.
```

This means that the worker is connected to RabbitMQ and is waiting for a
message. It does not mean that model training has started.

## Processing a Job

The backend must first create a job with the `QUEUED` status in PostgreSQL.

It then publishes a message to the `model-training-jobs` RabbitMQ queue:

```json
{
  "job_id": "d36ca66a-1ca8-47ad-9f02-c3c6b70597bd"
}
```

After receiving the message, the worker:

1. Validates the message.
2. Claims the corresponding PostgreSQL job.
3. Changes its status from `QUEUED` to `RUNNING`.
4. Exports current demand data from PostgreSQL.
5. Runs model selection, evaluation and production training.
6. Exports the model bundle.
7. Uploads the bundle to S3-compatible storage.
8. Changes the job status to `COMPLETED`.

If processing fails, the worker records the failure and changes the job status
to `FAILED`.

## Model Bundle Location

By default, the worker generates the following S3 prefix:

```text
models/bars/{bar_id}/jobs/{job_id}
```

For example:

```text
models/bars/17/jobs/d36ca66a-1ca8-47ad-9f02-c3c6b70597bd
```

The bundle contains:

```text
xgb_model.json
preprocessor.joblib
cleaner_artifacts.json
metadata.json
```

The final prefix is stored in `model_training_job.model_bundle_prefix`.

## Verify Image Contents

Verify that the required imports and SQL query are available:

```bash
docker compose run --rm --no-deps training python -c "import ml_common, boto3, training.worker; from pathlib import Path; print('imports: OK'); print('query:', Path('/app/infrastructure/postgres/query_v2.sql').exists())"
```

Expected output:

```text
imports: OK
query: True
```

## Rebuild After Changes

After changing training code, dependencies or the Dockerfile, rebuild and
restart the service:

```bash
docker compose build training
docker compose up -d training
```

## Stop the Worker

Stop only the training worker:

```bash
docker compose stop training
```

Stop all project services:

```bash
docker compose down
```

Named PostgreSQL, RabbitMQ and MinIO volumes are preserved unless they are
explicitly removed.
