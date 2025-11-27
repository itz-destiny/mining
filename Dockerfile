# Simple Dockerfile for the Flask simulated mining backend
FROM python:3.11-slim
WORKDIR /app

# Copy backend files
COPY backend /app

# Copy frontend files to expected location
COPY frontend /frontend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
ENV FLASK_ENV=production
CMD ["python", "server.py"]
