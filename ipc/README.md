# IPC Simulation Service

A Dockerized FastAPI microservice that simulates Inter-Process Communication (IPC) concepts like pipes and shared memory.

## Setup Instructions

1. Make sure you have Docker installed on your system

2. Navigate to the project directory:
```bash
cd CD_proj/ipc
```

3. Make the run_sim.sh script executable:
```bash
chmod +x run_sim.sh
```

4. Build the Docker image:
```bash
docker build -t ipc-simulator .
```

5. Run the Docker container:
```bash
docker run -p 8000:8000 ipc-simulator
```

## API Documentation

Access the interactive API documentation at:
```
http://localhost:8000/docs
```

## Shared Memory Simulation

### Endpoints

1. **Initialize Shared Memory**
   - URL: `http://localhost:8000/simulate/shared_memory/init`
   - Method: GET
   - Response:
     ```json
     {
       "status": "success",
       "message": "Shared memory initialized"
     }
     ```

2. **Write to Shared Memory**
   - URL: `http://localhost:8000/simulate/shared_memory/write?message=Hello`
   - Method: GET
   - Parameters:
     - message: string (required)
   - Response:
     ```json
     {
       "status": "success",
       "message": "Message written: Hello"
     }
     ```

3. **Read from Shared Memory**
   - URL: `http://localhost:8000/simulate/shared_memory/read`
   - Method: GET
   - Response:
     ```json
     {
       "status": "success",
       "message": "Message read: Hello"
     }
     ```

4. **Cleanup Shared Memory**
   - URL: `http://localhost:8000/simulate/shared_memory/cleanup`
   - Method: GET
   - Response:
     ```json
     {
       "status": "success",
       "message": "Shared memory cleaned up"
     }
     ```

## Pipe Simulation

### Endpoints

1. **Initialize Pipe**
   - URL: `http://localhost:8000/simulate/pipe/init`
   - Method: GET
   - Response:
     ```json
     {
       "status": "success",
       "message": "Pipe initialized"
     }
     ```

2. **Write to Pipe**
   - URL: `http://localhost:8000/simulate/pipe/write?message=Hello`
   - Method: GET
   - Parameters:
     - message: string (required)
   - Response:
     ```json
     {
       "status": "success",
       "message": "Message written to pipe: Hello"
     }
     ```

3. **Read from Pipe**
   - URL: `http://localhost:8000/simulate/pipe/read`
   - Method: GET
   - Response:
     ```json
     {
       "status": "success",
       "message": "Message read from pipe: Hello"
     }
     ```

4. **Cleanup Pipe**
   - URL: `http://localhost:8000/simulate/pipe/cleanup`
   - Method: GET
   - Response:
     ```json
     {
       "status": "success",
       "message": "Pipe cleaned up"
     }
     ```

## Usage Instructions

### Using the Swagger UI

1. Open `http://localhost:8000/docs` in your browser
2. Click on the desired endpoint
3. Click "Try it out"
4. Enter required parameters
5. Click "Execute"

### Using curl

Shared Memory Example:
```bash
# Initialize
curl "http://localhost:8000/simulate/shared_memory/init"

# Write
curl "http://localhost:8000/simulate/shared_memory/write?message=Hello"

# Read
curl "http://localhost:8000/simulate/shared_memory/read"

# Cleanup
curl "http://localhost:8000/simulate/shared_memory/cleanup"
```

Pipe Example:
```bash
# Initialize
curl "http://localhost:8000/simulate/pipe/init"

# Write
curl "http://localhost:8000/simulate/pipe/write?message=Hello"

# Read
curl "http://localhost:8000/simulate/pipe/read"

# Cleanup
curl "http://localhost:8000/simulate/pipe/cleanup"
```

## Important Notes

1. **Order of Operations**:
   - Always follow the sequence: init → write → read → cleanup
   - Operations must be performed in order

2. **Error Handling**:
   - Reading before writing will result in an error
   - Writing before initializing will result in an error
   - Initializing twice will result in an error

3. **Cleanup**:
   - Always perform cleanup after testing
   - This ensures a fresh start for the next test

4. **Port**:
   - Make sure port 8000 is available
   - If port 8000 is in use, you can change it in the docker run command
