# Model Training Job Contract

**Status:** Draft

## Purpose

This document defines the communication contract between the backend and the training worker.

Model training is executed asynchronously. PostgreSQL stores the job details and current status, while RabbitMQ notifies the training worker that a job is ready to be processed.

The resulting production model bundle is uploaded to S3-compatible storage.

## Responsibilities

The backend:

- stores uploaded sales data in PostgreSQL;
- creates a training job with the `QUEUED` status;
- publishes the job identifier through RabbitMQ;
- reads the job status from PostgreSQL;
- exposes the job status to the frontend.

The training worker:

- consumes job identifiers from RabbitMQ;
- loads job details from PostgreSQL;
- updates the job status;
- executes the training pipeline;
- uploads the production model bundle to S3-compatible storage;
- stores the model bundle location in the job record.

## RabbitMQ Message

Queue name:

`model-training-jobs`

The RabbitMQ message contains only the identifier of a job that already exists in PostgreSQL.

The message body is encoded as JSON:

```json
{
  "job_id": "d36ca66a-1ca8-47ad-9f02-c3c6b70597bd"
}
```

### Message Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `job_id` | UUID string | yes | Identifier of the training job stored in PostgreSQL |

Training data and model parameters must not be included directly in the RabbitMQ message. They are loaded from the database using `job_id`.

## Database Record

Suggested table name:

`model_training_job`

The backend creates the record before publishing the RabbitMQ message.

### Job Fields

| Column | Type | Required | Description |
|---|---|---:|---|
| `job_id` | UUID | yes | Unique training job identifier |
| `bar_id` | INTEGER | yes | Bar for which the model is trained |
| `status` | VARCHAR | yes | Current job status |
| `model_bundle_prefix` | TEXT | no | S3 prefix containing the completed model bundle |
| `error_message` | TEXT | no | Description of a training failure |
| `created_at` | TIMESTAMPTZ | yes | Time when the backend created the job |
| `started_at` | TIMESTAMPTZ | no | Time when training started |
| `finished_at` | TIMESTAMPTZ | no | Time when training completed or failed |

Additional fields describing the exact training dataset may be added after the data selection strategy is agreed upon.

The database migration is the source of truth for the physical table definition.

## Job Statuses

The initial implementation supports the following statuses:

- `QUEUED`
- `RUNNING`
- `COMPLETED`
- `FAILED`

Expected transitions:

```text
QUEUED -> RUNNING -> COMPLETED
                  -> FAILED
```

The backend creates a job with the `QUEUED` status.

The training worker changes the status to `RUNNING` before starting the training pipeline.

After successful training and model upload, the worker changes the status to `COMPLETED`.

If training or model upload fails, the worker changes the status to `FAILED` and stores an error description.

## Job Claiming

Only jobs with the `QUEUED` status may be started.

The worker must claim a job using a conditional database operation that changes its status from `QUEUED` to `RUNNING`.

If the job does not exist or is no longer `QUEUED`, the worker must not start another training run.

This prevents duplicate RabbitMQ deliveries from starting the same job more than once.

## Processing Flow

1. The backend receives and stores uploaded sales data.
2. The backend creates a training job with the `QUEUED` status.
3. The backend publishes the job identifier to RabbitMQ.
4. The training worker receives and validates the message.
5. The worker loads the job details from PostgreSQL.
6. The worker claims the job and changes its status to `RUNNING`.
7. The worker loads the required sales data.
8. The worker executes the training pipeline.
9. The worker uploads the production model bundle to S3-compatible storage.
10. The worker stores the model bundle prefix and changes the status to `COMPLETED`.
11. The worker acknowledges the RabbitMQ message.

If training fails, the worker stores the error, changes the status to `FAILED` and then acknowledges the message.

Invalid RabbitMQ messages must not start a training job.

## Model Bundle

After successful training, `model_bundle_prefix` points to the production model bundle in S3-compatible storage.

Example:

```text
models/bars/17/jobs/d36ca66a-1ca8-47ad-9f02-c3c6b70597bd
```

A job must not be marked as `COMPLETED` before the complete model bundle has been uploaded successfully.

## Open Questions

The following decisions must be confirmed before the database schema and worker implementation are finalized:

- Does a job use all available data for its `bar_id`?
- Should the job contain a cutoff date defining the latest included sales day?
- Should the job refer to a specific data upload or dataset snapshot?
- Should RabbitMQ messages include a schema version?
- How should jobs left in the `RUNNING` status after a worker failure be recovered?
- Should failed jobs be retried automatically or only through a new job created by the backend?
- Is `model_bundle_prefix` provided by the backend or generated by the training worker?
