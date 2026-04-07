FROM python:3.12-slim

WORKDIR /app

# Install production dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create the persistent volume mount point for the SQLite database
RUN mkdir -p /data

# Copy project metadata (read at runtime by /about command)
COPY pyproject.toml .

# Copy source code
COPY src/ src/

# Set PYTHONPATH so "python -m bot" finds the bot package in src/
ENV PYTHONPATH=/app/src

# Default DATABASE_URL points at the Railway persistent volume mount.
# Four slashes = three from sqlite:/// + one for the absolute path /data/…
ENV DATABASE_URL=sqlite+aiosqlite:////data/adventurer-sheet.db

CMD ["python", "-m", "bot"]

