from collections.abc import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel

from training.messaging.rabbitmq_config import RabbitMQConfig

MessageHandler = Callable[
    [
        BlockingChannel,
        pika.spec.Basic.Deliver,
        pika.BasicProperties,
        bytes,
    ],
    None,
]


class RabbitMQClient:
    """Manage the RabbitMQ connection and message consumption."""

    def __init__(self, config: RabbitMQConfig) -> None:
        self._config = config
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None

    def connect(self) -> None:
        """Connect to RabbitMQ and prepare the training queue."""

        if self._connection is not None and self._connection.is_open:
            return

        credentials = pika.PlainCredentials(
            username=self._config.username,
            password=self._config.password,
        )

        parameters = pika.ConnectionParameters(
            host=self._config.host,
            port=self._config.port,
            credentials=credentials,
        )

        self._connection = pika.BlockingConnection(parameters)

        self._channel = self._connection.channel()

        self._channel.queue_declare(
            queue=self._config.queue_name,
            durable=True,
        )

        self._channel.basic_qos(prefetch_count=1)

    def start_consuming(self, handler: MessageHandler) -> None:
        """Consume training request using the provided callback."""

        if self._channel is None:
            self.connect()

        channel = self._require_channel()

        channel.basic_consume(
            queue=self._config.queue_name,
            on_message_callback=handler,
            auto_ack=False,
        )
        channel.start_consuming()

    def close(self) -> None:
        """Close the RabbitMQ connection."""

        if self._connection is not None and self._connection.is_open:
            self._connection.close()

        self._channel = None
        self._connection = None

    def _require_channel(self) -> BlockingChannel:
        if self._channel is None:
            raise RuntimeError("RabbitMQ channel is not available.")

        return self._channel
