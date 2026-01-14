# Expense Tracker Telegram Bot
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Environment variables (set at runtime)
ENV PYTHONUNBUFFERED=1

# Run bot
CMD ["python", "-m", "src.bot.main"]
