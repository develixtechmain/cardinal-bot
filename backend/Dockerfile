FROM python:3.13-slim

LABEL loki.include=true loki.service.name=backend_core

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
