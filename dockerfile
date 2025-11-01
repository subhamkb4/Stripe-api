# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Expose port 5000 (or whatever PORT Render sets)
EXPOSE 5000

# Run the app with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
