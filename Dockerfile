# Use Python 3.11 as the base image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app/

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project into the working directory
COPY . .

# Navigate to the directory containing manage.py
WORKDIR /app/geobackend

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations (if needed for SQLite)
RUN python manage.py migrate

# Expose port 8000 for the Django application
EXPOSE 8000

# Start the Django server using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "geobackend.wsgi:application"]
