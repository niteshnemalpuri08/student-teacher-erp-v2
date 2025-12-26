
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r backend/requirements.txt || pip install flask flask-cors numpy pandas scikit-learn
EXPOSE 5000
CMD ["python", "backend/server.py"]
