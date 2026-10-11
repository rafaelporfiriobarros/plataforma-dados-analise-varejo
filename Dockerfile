FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir pandas "psycopg[binary]" python-dotenv
COPY . .
ENV PYTHONPATH=/app/src
CMD ["python", "-m", "mercado_analytics.pipeline"]
