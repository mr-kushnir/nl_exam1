# Expense Tracker Telegram Bot
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run FastAPI with uvicorn for webhook mode
CMD ["python", "-m", "uvicorn", "src.bot.main:app", "--host", "0.0.0.0", "--port", "8080"]
