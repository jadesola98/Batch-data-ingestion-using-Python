FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer between code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingest_data.py .

ENTRYPOINT ["python", "ingest_data.py"]
