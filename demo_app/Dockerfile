FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt Flask psutil mongomock pymongo requests
COPY . .
ENV PYTHONPATH=/app
CMD ["python", "demo_app/app.py"]
