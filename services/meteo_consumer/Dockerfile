FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/meteo_consumer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/meteo_consumer/src ./src

CMD ["python", "-m", "src.main"]
