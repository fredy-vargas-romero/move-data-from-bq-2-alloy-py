FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and SQL files
COPY src/ ./src/
COPY sql/ ./sql/

EXPOSE 8080

CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--timeout", "30", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "--preload", "src.main:app"]
