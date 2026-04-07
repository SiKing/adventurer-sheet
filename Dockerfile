FROM python:3.12-slim

WORKDIR /app

# Install production dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project metadata (read at runtime by /about command)
COPY pyproject.toml .

# Copy source code
COPY src/ src/

# Set PYTHONPATH so "python -m bot" finds the bot package in src/
ENV PYTHONPATH=/app/src
CMD ["python", "-m", "bot"]

