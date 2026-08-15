FROM python:3.12-slim
WORKDIR /app/training
RUN pip install poetry
COPY --from=ml_common . /app/ml_common
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root
COPY src/ ./src/
COPY --from=postgres_queries /query_v2.sql \
    /app/infrastructure/postgres/query_v2.sql
ENV PYTHONPATH=/app/training/src
CMD ["python", "-m", "training.worker"]
