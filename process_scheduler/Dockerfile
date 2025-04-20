FROM python:3.9-slim

WORKDIR /app

# Copy everything from your project directory into the Docker image
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
