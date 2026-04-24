FROM python:3.12-slim
WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root
COPY src/ ./src/
COPY data/ ./data/
ENV PYTHONPATH=/app/src
CMD ["python", "-m", "training.main"]
