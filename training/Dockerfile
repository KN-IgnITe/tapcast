FROM python:3.12-slim
WORKDIR /app/training
RUN pip install poetry
COPY ml_common /app/ml_common
COPY training/pyproject.toml training/poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root
COPY training/src/ ./src/
COPY infrastructure /app/infrastructure
ENV PYTHONPATH=/app/training/src
CMD ["python", "-m", "training.worker"]
