# CC-VirtualLabs Integrated Microservices

This repository contains an integrated collection of microservices for Computer Science education, specifically focused on Operating System concepts. Each microservice is containerized using Docker and can be run independently or as part of the complete system.

## Services Overview

The system consists of 8 microservices, each focusing on different aspects of Operating Systems:

1. **IPC Service** (Port: 8000)
   - Inter-Process Communication simulation
   - Demonstrates various IPC mechanisms
   - Built on FastAPI with Python

2. **System Call Service** (Port: 8001)
   - System call simulation and visualization
   - Demonstrates OS system call operations
   - Python-based implementation

3. **Memory Manager Service** (Port: 8002)
   - Memory management simulation
   - Includes paging, segmentation, and memory allocation
   - Python implementation

4. **Process Scheduler Service** (Port: 8003)
   - Process scheduling algorithms simulation
   - Includes FCFS, Round Robin, Priority Scheduling
   - Python-based implementation

5. **Multithreading Service** (Port: 8004)
   - Thread management and synchronization
   - Demonstrates thread creation, management, and synchronization
   - FastAPI implementation

6. **File System Service** (Port: 8005)
   - File system operations simulation
   - Demonstrates file operations and management
   - Python implementation

7. **Deadlock Simulator Service** (Port: 8006)
   - Deadlock detection and prevention
   - Resource allocation graph visualization
   - Python-based implementation

8. **Concurrency Simulator Service** (Port: 8007)
   - Concurrent process execution simulation
   - Race condition demonstration
   - FastAPI implementation

## Prerequisites

- Docker
- Docker Compose
- Git

## 

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/CC-VirtualLabs-integrate.git
   cd CC-VirtualLabs-integrate
   ```

2. **Start All Services**
   ```bash
   docker-compose up --build
   ```
   This will build and start all services in detached mode.

3. **Access Services**
   Each service is accessible on its respective port:
   - IPC Service: http://localhost:8000
   - System Call Service: http://localhost:8001
   - Memory Manager Service: http://localhost:8002
   - Process Scheduler Service: http://localhost:8003
   - Multithreading Service: http://localhost:8004
   - File System Service: http://localhost:8005
   - Deadlock Simulator Service: http://localhost:8006
   - Concurrency Simulator Service: http://localhost:8007

## 🛠️ Development

### Running Individual Services
To run a specific service:
```bash
docker-compose up <service-name>
```
Example:
```bash
docker-compose up ipc-service
```

### Viewing Logs
```bash
docker-compose logs -f <service-name>
```

### Stopping Services
```bash
docker-compose down
```

## Service Architecture

Each service follows a similar architecture:
- FastAPI-based REST API
- Docker containerization
- Volume mounting for live code updates
- Environment configuration for logging

## Configuration

The services are configured through the `docker-compose.yml` file. Key configurations include:
- Port mappings
- Volume mounts
- Environment variables
- Build contexts

## API Documentation

Each service provides its own API documentation at:
```
http://localhost:<port>/docs
```


## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Acknowledgments

- FastAPI for the web framework
- Docker for containerization
- All contributors and maintainers
