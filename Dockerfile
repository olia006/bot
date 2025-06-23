FROM python:3.9-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 2>&1 | tee pip_install.log || (cat pip_install.log && exit 1)

# Copy application code
COPY . .

CMD ["python", "bot.py"] 