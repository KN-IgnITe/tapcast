import logging

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pydantic import ValidationError

from training.jobs.training_job_request import TrainingJobRequest
from training.jobs.training_job_runner import TrainingJobRunner
from training.messaging.rabbitmq_client import RabbitMQClient

logger = logging.getLogger(__name__)


class TrainingJobConsumer:
    """Receive training requests and pass them to the job runner."""

    def __init__(
        self,
        client: RabbitMQClient,
        runner: TrainingJobRunner,
    ) -> None:
        self._client = client
        self._runner = runner

    def start(self) -> None:
        """Start consuming training requests."""

        logger.info("Waiting for training jobs.")
        self._client.start_consuming(self._handle_message)

    def _handle_message(
        self,
        channel: BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.BasicProperties,
        body: bytes,
    ) -> None:
        try:
            request = TrainingJobRequest.from_bytes(body)
            self._runner.run(request.job_id)

        except ValidationError as error:
            logger.warning("Rejecting invalid training job request: %s", error)
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )
            return

        except Exception:
            logger.exception("Training job processing failed.")
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )
            return

        channel.basic_ack(
            delivery_tag=method.delivery_tag,
        )
