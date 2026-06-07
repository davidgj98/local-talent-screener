FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV OLLAMA_HOST=http://ollama:11434

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
