FROM python:3.11-slim

LABEL loki.include=true loki.service.name=message_processor

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
