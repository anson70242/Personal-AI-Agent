# Use Python 3.10 slim image (Lightweight version)
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
# libpq-dev is required for building psycopg2 (PostgreSQL adapter)
# gcc is the compiler required for some Python packages
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies without caching install files to save space
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Start command: Use uvicorn to run the FastAPI app
# main:app refers to 'app' object in 'main.py'
# host 0.0.0.0 allows external access (essential for Docker)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]