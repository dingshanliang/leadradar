FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir .

COPY src/ src/
COPY data/ data/
COPY tests/ tests/

EXPOSE 8000

CMD ["uvicorn", "leadradar.main:app", "--host", "0.0.0.0", "--port", "8000"]
