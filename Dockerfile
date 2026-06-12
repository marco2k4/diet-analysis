FROM python:3.9-slim

WORKDIR /app

# Copy dependency list first (layer-cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default command runs the analysis
CMD ["python", "data_analysis.py"]
