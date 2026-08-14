from pathlib import Path

import pytest

from training.messaging.rabbitmq_config import RabbitMQConfig


def test_from_env_loads_rabbitmq_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RABBITMQ_HOST", "rabbitmq.internal")
    monkeypatch.setenv("RABBITMQ_PORT", "5673")
    monkeypatch.setenv("RABBITMQ_DEFAULT_USER", "training")
    monkeypatch.setenv("RABBITMQ_DEFAULT_PASS", "secret")
    monkeypatch.setenv("TRAINING_QUEUE_NAME", "training-jobs")

    config = RabbitMQConfig.from_env()

    assert config.host == "rabbitmq.internal"
    assert config.port == 5673
    assert config.username == "training"
    assert config.password == "secret"
    assert config.queue_name == "training-jobs"


def test_config_uses_connection_and_queue_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    config = RabbitMQConfig(
        username="training",
        password="secret",
    )  # type: ignore[call-arg]

    assert config.host == "localhost"
    assert config.port == 5672
    assert config.queue_name == "model-training-jobs"
