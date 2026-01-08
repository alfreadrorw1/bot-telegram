# Gunakan Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy semua file ke container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Jalankan bot
CMD ["python", "alfread.py"]