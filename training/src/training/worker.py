import logging
from pathlib import Path

from ml_common.artifacts.s3_model_bundle_store import (
    S3ModelBundleStore,
)
from ml_common.storage.s3_client import S3Client
from ml_common.storage.s3_config import S3Config

from training.data.sql_to_json_exporter import (
    ExporterPaths,
    SQLToJSONExporter,
)
from training.database.database_client import DatabaseClient
from training.database.database_config import DatabaseConfig
from training.database.postgres_training_job_repository import (
    PostgresTrainingJobRepository,
)
from training.features.history_cleaner import HistoryCleanerConfig
from training.jobs.demand_training_pipeline import DemandTrainingPipeline
from training.jobs.training_job_consumer import TrainingJobConsumer
from training.jobs.training_job_runner import TrainingJobRunner
from training.messaging.rabbitmq_client import RabbitMQClient
from training.messaging.rabbitmq_config import RabbitMQConfig


def main() -> None:
    """Start the model training worker."""

    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s %(levelname)s " "%(name)s: %(message)s"),
    )

    database_config = DatabaseConfig()  # type: ignore[call-arg]
    rabbitmq_config = RabbitMQConfig.from_env()
    s3_config = S3Config()  # type: ignore[call-arg]

    project_dir = Path(__file__).resolve().parents[2]
    artifact_root = project_dir / "artifacts" / "jobs"

    cleaning_config = HistoryCleanerConfig(
        winsorized_quantile=0.99,
        min_winsorization_observations=20,
        enable_winsorization=True,
        enable_oos_imputation=False,
    )

    with (
        DatabaseClient(database_config) as database_client,
        S3Client(s3_config) as s3_client,
    ):
        s3_client.ensure_bucket_exists()

        repository = PostgresTrainingJobRepository(database_client)

        data_exporter = SQLToJSONExporter(
            client=database_client,
            paths=ExporterPaths.resolve_defaults(),
        )

        model_bundle_store = S3ModelBundleStore(s3_client)

        pipeline = DemandTrainingPipeline(
            data_exporter=data_exporter,
            model_bundle_store=model_bundle_store,
            artifact_root=artifact_root,
            cleaning_config=cleaning_config,
        )

        runner = TrainingJobRunner(
            repository=repository,
            pipeline=pipeline,
        )

        rabbitmq_client = RabbitMQClient(rabbitmq_config)
        consumer = TrainingJobConsumer(
            client=rabbitmq_client,
            runner=runner,
        )

        try:
            consumer.start()
        except KeyboardInterrupt:
            logging.getLogger(__name__).info("Training worker interrupted.")
        finally:
            rabbitmq_client.close()


if __name__ == "__main__":
    main()
