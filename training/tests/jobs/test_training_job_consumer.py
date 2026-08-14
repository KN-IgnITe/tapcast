import json
from unittest.mock import MagicMock
from uuid import UUID

import pika
import pytest
from pika.adapters.blocking_connection import BlockingChannel

from training.jobs.training_job_consumer import TrainingJobConsumer
from training.jobs.training_job_runner import TrainingJobRunner
from training.messaging.rabbitmq_client import RabbitMQClient


@pytest.fixture
def rabbitmq_client() -> MagicMock:
    return MagicMock(spec=RabbitMQClient)


@pytest.fixture
def runner() -> MagicMock:
    return MagicMock(spec=TrainingJobRunner)


@pytest.fixture
def consumer(
    rabbitmq_client: MagicMock,
    runner: MagicMock,
) -> TrainingJobConsumer:
    return TrainingJobConsumer(rabbitmq_client, runner)


@pytest.fixture
def channel() -> MagicMock:
    return MagicMock(spec=BlockingChannel)


@pytest.fixture
def delivery() -> MagicMock:
    method = MagicMock(spec=pika.spec.Basic.Deliver)
    method.delivery_tag = 42
    return method


@pytest.fixture
def properties() -> MagicMock:
    return MagicMock(spec=pika.BasicProperties)


def test_start_registers_consumer_handler(
    consumer: TrainingJobConsumer,
    rabbitmq_client: MagicMock,
) -> None:
    consumer.start()

    rabbitmq_client.start_consuming.assert_called_once_with(consumer._handle_message)


def test_valid_message_runs_job_and_is_acknowledged(
    consumer: TrainingJobConsumer,
    runner: MagicMock,
    channel: MagicMock,
    delivery: MagicMock,
    properties: MagicMock,
    job_id: UUID,
) -> None:
    body = json.dumps({"job_id": str(job_id)}).encode("utf-8")

    consumer._handle_message(channel, delivery, properties, body)

    runner.run.assert_called_once_with(job_id)
    channel.basic_ack.assert_called_once_with(delivery_tag=42)
    channel.basic_nack.assert_not_called()


def test_invalid_message_is_rejected_without_running_job(
    consumer: TrainingJobConsumer,
    runner: MagicMock,
    channel: MagicMock,
    delivery: MagicMock,
    properties: MagicMock,
) -> None:
    consumer._handle_message(channel, delivery, properties, b"invalid")

    runner.run.assert_not_called()
    channel.basic_nack.assert_called_once_with(
        delivery_tag=42,
        requeue=False,
    )
    channel.basic_ack.assert_not_called()


def test_runner_failure_is_rejected_without_acknowledgement(
    consumer: TrainingJobConsumer,
    runner: MagicMock,
    channel: MagicMock,
    delivery: MagicMock,
    properties: MagicMock,
    job_id: UUID,
) -> None:
    runner.run.side_effect = RuntimeError("Database update failed.")
    body = json.dumps({"job_id": str(job_id)}).encode("utf-8")

    consumer._handle_message(channel, delivery, properties, body)

    channel.basic_nack.assert_called_once_with(
        delivery_tag=42,
        requeue=False,
    )
    channel.basic_ack.assert_not_called()
