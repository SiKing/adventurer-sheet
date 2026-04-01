FROM python:3.12-slim

WORKDIR /app

# Install production dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/

# Run from the src directory so "python -m bot" resolves correctly
WORKDIR /app/src
CMD ["python", "-m", "bot"]

