# Use the official Python image with the desired version
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1  
ENV PYTHONUNBUFFERED 1    
ENV DJANGO_SETTINGS_MODULE=Website1.settings  

# Set working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*


# Install Python dependencies
COPY requirements.txt /app/

RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files into the container
COPY . /app/

# Expose the port your app runs on
EXPOSE 8000

# Run the application
CMD ["gunicorn", "Website1.wsgi:application", "-b", "0.0.0.0:8000"]
