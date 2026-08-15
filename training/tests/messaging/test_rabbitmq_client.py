from unittest.mock import MagicMock

import pika
import pytest

from training.messaging.rabbitmq_client import RabbitMQClient
from training.messaging.rabbitmq_config import RabbitMQConfig


@pytest.fixture
def config() -> RabbitMQConfig:
    return RabbitMQConfig(
        host="rabbitmq.internal",
        port=5673,
        username="training",
        password="secret",
        queue_name="training-jobs",
    )


def test_connect_opens_connection_and_prepares_queue(
    config: RabbitMQConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials = object()
    parameters = object()
    channel = MagicMock()
    connection = MagicMock()
    connection.is_open = True
    connection.channel.return_value = channel

    credentials_factory = MagicMock(return_value=credentials)
    parameters_factory = MagicMock(return_value=parameters)
    connection_factory = MagicMock(return_value=connection)
    monkeypatch.setattr(pika, "PlainCredentials", credentials_factory)
    monkeypatch.setattr(pika, "ConnectionParameters", parameters_factory)
    monkeypatch.setattr(pika, "BlockingConnection", connection_factory)

    client = RabbitMQClient(config)
    client.connect()

    credentials_factory.assert_called_once_with(
        username="training",
        password="secret",
    )
    parameters_factory.assert_called_once_with(
        host="rabbitmq.internal",
        port=5673,
        credentials=credentials,
    )
    connection_factory.assert_called_once_with(parameters)
    channel.queue_declare.assert_called_once_with(
        queue="training-jobs",
        durable=True,
    )
    channel.basic_qos.assert_called_once_with(prefetch_count=1)


def test_connect_reuses_open_connection(
    config: RabbitMQConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection_factory = MagicMock()
    monkeypatch.setattr(pika, "BlockingConnection", connection_factory)

    client = RabbitMQClient(config)
    connection = MagicMock()
    connection.is_open = True
    client._connection = connection

    client.connect()

    connection_factory.assert_not_called()


def test_start_consuming_registers_handler(
    config: RabbitMQConfig,
) -> None:
    client = RabbitMQClient(config)
    channel = MagicMock()
    client._channel = channel
    handler = MagicMock()

    client.start_consuming(handler)

    channel.basic_consume.assert_called_once_with(
        queue="training-jobs",
        on_message_callback=handler,
        auto_ack=False,
    )
    channel.start_consuming.assert_called_once_with()


def test_close_closes_connection_and_clears_state(
    config: RabbitMQConfig,
) -> None:
    client = RabbitMQClient(config)
    connection = MagicMock()
    connection.is_open = True
    client._connection = connection
    client._channel = MagicMock()

    client.close()

    connection.close.assert_called_once_with()
    assert client._connection is None
    assert client._channel is None


def test_require_channel_raises_when_channel_is_missing(
    config: RabbitMQConfig,
) -> None:
    client = RabbitMQClient(config)

    with pytest.raises(
        RuntimeError,
        match="RabbitMQ channel is not available",
    ):
        client._require_channel()
