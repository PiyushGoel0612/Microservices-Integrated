FROM gcc:latest

WORKDIR /app
COPY . .

RUN apt update && apt install -y python3-pip python3-venv

# Create and activate virtual environment
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install Python packages in virtual environment
RUN pip install fastapi uvicorn

# Make run_sim.sh executable
RUN chmod +x run_sim.sh

CMD ["/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
