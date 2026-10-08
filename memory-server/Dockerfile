FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py racing.py ./
USER nobody
CMD ["python", "server.py"]
