FROM python:3.12-slim
WORKDIR /app
COPY worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY worker/pipeline.py ./pipeline.py
ENV PYTHONUNBUFFERED=1 INTERVAL_SECONDS=86400 DATABASE_PATH=/data/observations.sqlite3
CMD ["python","pipeline.py"]
