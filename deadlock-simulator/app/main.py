from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Set
import uuid
import requests

USER = "user1"

def send_analytics_event(user_id: str, lab_type: str, event_type: str, event_data: dict):
    url = "http://usage-analytics:8000/analytics/event"
    payload = {
        "user_id": user_id,
        "lab_type": lab_type,
        "event_type": event_type,
        "event_data": event_data
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Analytics] Failed to send event: {e}")

def send_lab_completion(user_id: str, lab_type: str, completion_time: int, success, errors, resources_used: dict):
    url = "http://performance-reporting:8000/performance/record"
    payload = {
        "user_id": user_id,
        "lab_type": lab_type,
        "completion_time": completion_time,
        "success": success,
        "errors": errors,
        "resources_used": resources_used
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Analytics] Failed to report event: {e}")

app = FastAPI()

class Resource:
    def __init__(self, name: str, units: int = 1):
        self.id = str(uuid.uuid4())
        self.name = name
        self.units = units  # Total units available
        self.allocated = {}  # process_id -> units allocated
        self.requested = {}  # process_id -> units requested

class Process:
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.allocated_resources = {}  # resource_id -> units
        self.requested_resources = {}  # resource_id -> units
        self.max_resources = {}  # resource_id -> max units needed
        self.status = "active"  # active, blocked, terminated

class DeadlockSimulator:
    def __init__(self):
        self.processes = {}  # id -> Process
        self.resources = {}  # id -> Resource
        self.allocation_graph = {}  # {process_id: {resource_id: units}}
        self.request_graph = {}  # {process_id: {resource_id: units}}
        
    def create_process(self, name: str) -> Process:
        process = Process(name)
        self.processes[process.id] = process
        self.allocation_graph[process.id] = {}
        self.request_graph[process.id] = {}
        return process
    
    def create_resource(self, name: str, units: int = 1) -> Resource:
        resource = Resource(name, units)
        self.resources[resource.id] = resource
        return resource
    
    def request_resource(self, process_id: str, resource_id: str, units: int = 1) -> bool:
        """Process requests resources. Returns whether request was granted immediately."""
        if process_id not in self.processes:
            raise ValueError(f"Process {process_id} not found")
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} not found")
            
        process = self.processes[process_id]
        resource = self.resources[resource_id]
        
        # Check if enough units are available
        allocated_units = sum(resource.allocated.values(), 0)
        available_units = resource.units - allocated_units
        
        # Record the request
        resource.requested[process_id] = units
        process.requested_resources[resource_id] = units
        self.request_graph[process_id][resource_id] = units
        
        # If resources available, allocate immediately
        if available_units >= units:
            if process_id in resource.allocated:
                resource.allocated[process_id] += units
            else:
                resource.allocated[process_id] = units
                
            if resource_id in process.allocated_resources:
                process.allocated_resources[resource_id] += units
            else:
                process.allocated_resources[resource_id] = units
                
            self.allocation_graph[process_id][resource_id] = units
            
            # Clear the request since it's been granted
            del resource.requested[process_id]
            del process.requested_resources[resource_id]
            del self.request_graph[process_id][resource_id]
            
            return True
        else:
            # Request can't be granted now, process becomes blocked
            process.status = "blocked"
            return False
    
    def release_resource(self, process_id: str, resource_id: str, units: Optional[int] = None) -> bool:
        """Process releases resources. If units is None, release all allocated units."""
        if process_id not in self.processes:
            raise ValueError(f"Process {process_id} not found")
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} not found")
            
        process = self.processes[process_id]
        resource = self.resources[resource_id]
        
        if process_id not in resource.allocated:
            return False  # Nothing to release
            
        # Determine how many units to release
        if units is None or units >= resource.allocated[process_id]:
            units_to_release = resource.allocated[process_id]
            del resource.allocated[process_id]
            del process.allocated_resources[resource_id]
            if resource_id in self.allocation_graph[process_id]:
                del self.allocation_graph[process_id][resource_id]
        else:
            units_to_release = units
            resource.allocated[process_id] -= units
            process.allocated_resources[resource_id] -= units
            self.allocation_graph[process_id][resource_id] = resource.allocated[process_id]
            
        # Try to satisfy waiting requests
        self._try_satisfy_waiting_requests(resource_id)
        
        return True
    
    def _try_satisfy_waiting_requests(self, resource_id: str):
        """Try to satisfy waiting requests for a resource that has freed units."""
        resource = self.resources[resource_id]
        allocated_units = sum(resource.allocated.values(), 0)
        available_units = resource.units - allocated_units
        
        # Nothing to do if no units available
        if available_units == 0:
            return
            
        # Try to satisfy waiting requests
        satisfied_processes = []
        
        for pid, requested_units in resource.requested.items():
            if requested_units <= available_units:
                process = self.processes[pid]
                
                # Allocate the resource
                if pid in resource.allocated:
                    resource.allocated[pid] += requested_units
                else:
                    resource.allocated[pid] = requested_units
                    
                if resource_id in process.allocated_resources:
                    process.allocated_resources[resource_id] += requested_units
                else:
                    process.allocated_resources[resource_id] = requested_units
                    
                self.allocation_graph[pid][resource_id] = requested_units
                
                # Update available units
                available_units -= requested_units
                
                # Unblock the process
                process.status = "active"
                
                # Mark this request as satisfied
                satisfied_processes.append(pid)
                
                # If no more units, stop trying
                if available_units == 0:
                    break
        
        # Remove satisfied requests
        for pid in satisfied_processes:
            del resource.requested[pid]
            del self.processes[pid].requested_resources[resource_id]
            if pid in self.request_graph and resource_id in self.request_graph[pid]:
                del self.request_graph[pid][resource_id]
    
    def detect_deadlock(self) -> Dict:
        """Detect deadlocks using the wait-for graph method."""
        # Build wait-for graph
        wait_for_graph = {}
        
        for p_id, p_requests in self.request_graph.items():
            if not p_requests:  # No requests, so not waiting
                continue
                
            wait_for_graph[p_id] = set()
            
            for r_id, _ in p_requests.items():
                # Find all processes that have allocated this resource
                for other_p_id in self.resources[r_id].allocated:
                    if other_p_id != p_id:
                        wait_for_graph[p_id].add(other_p_id)
        
        # Find cycles in the wait-for graph
        deadlocked_processes = self._find_cycles(wait_for_graph)
        
        return {
            "deadlock_detected": len(deadlocked_processes) > 0,
            "deadlocked_processes": [
                {"id": p_id, "name": self.processes[p_id].name}
                for p_id in deadlocked_processes
            ]
        }
    
    def _find_cycles(self, graph: Dict[str, Set[str]]) -> Set[str]:
        """Find cycles in the wait-for graph using DFS."""
        visited = set()
        rec_stack = set()
        deadlocked = set()
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            
            if node in graph:
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if dfs(neighbor):
                            deadlocked.add(node)
                            return True
                    elif neighbor in rec_stack:
                        deadlocked.add(node)
                        return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                dfs(node)
                
        return deadlocked
    
    def get_system_state(self) -> Dict:
        """Get the current state of the system for visualization."""
        return {
            "processes": [
                {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status,
                    "allocated": p.allocated_resources,
                    "requested": p.requested_resources
                }
                for p in self.processes.values()
            ],
            "resources": [
                {
                    "id": r.id,
                    "name": r.name,
                    "units": r.units,
                    "allocated": r.allocated,
                    "requested": r.requested
                }
                for r in self.resources.values()
            ],
            "allocation_graph": self.allocation_graph,
            "request_graph": self.request_graph
        }
    
    def reset(self):
        """Reset the simulation."""
        self.processes = {}
        self.resources = {}
        self.allocation_graph = {}
        self.request_graph = {}

# Initialize simulator
simulator = DeadlockSimulator()

# Request models
class ProcessRequest(BaseModel):
    name: str

class ResourceRequest(BaseModel):
    name: str
    units: int = 1

class ResourceAllocationRequest(BaseModel):
    resource_id: str
    units: int = 1

class ResourceReleaseRequest(BaseModel):
    resource_id: str
    units: Optional[int] = None

# Process endpoints
@app.post("/processes/")
def create_process(req: ProcessRequest):
    process = simulator.create_process(req.name)

    send_analytics_event(
        user_id=USER,
        lab_type="deadlock-sim",
        event_type="create_process",
        event_data={"process_id": process.id, "process_name": process.name}
    )

    return {
        "id": process.id,
        "name": process.name,
        "status": process.status
    }

@app.get("/processes/")
def list_processes():
    return {
        "processes": [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status,
                "allocated": p.allocated_resources,
                "requested": p.requested_resources
            }
            for p in simulator.processes.values()
        ]
    }

@app.get("/processes/{process_id}")
def get_process(process_id: str):
    if process_id not in simulator.processes:
        raise HTTPException(status_code=404, detail="Process not found")
    
    p = simulator.processes[process_id]
    return {
        "id": p.id,
        "name": p.name,
        "status": p.status,
        "allocated": p.allocated_resources,
        "requested": p.requested_resources
    }

# Resource endpoints
@app.post("/resources/")
def create_resource(req: ResourceRequest):
    resource = simulator.create_resource(req.name, req.units)
    
    send_analytics_event(
        user_id=USER,
        lab_type="deadlock-sim",
        event_type="create_resource",
        event_data={"resource_id": resource.id, 
                    "resource_name": resource.name, 
                    "resource_units": resource.units}
    )

    return {
        "id": resource.id,
        "name": resource.name,
        "units": resource.units
    }

@app.get("/resources/")
def list_resources():
    return {
        "resources": [
            {
                "id": r.id,
                "name": r.name,
                "units": r.units,
                "allocated": r.allocated,
                "requested": r.requested
            }
            for r in simulator.resources.values()
        ]
    }

@app.get("/resources/{resource_id}")
def get_resource(resource_id: str):
    if resource_id not in simulator.resources:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    r = simulator.resources[resource_id]
    return {
        "id": r.id,
        "name": r.name,
        "units": r.units,
        "allocated": r.allocated,
        "requested": r.requested
    }

# Resource allocation endpoints
@app.post("/processes/{process_id}/request")
def request_resource(process_id: str, req: ResourceAllocationRequest):
    try:
        success = simulator.request_resource(process_id, req.resource_id, req.units)

        send_analytics_event(
            user_id=USER,
            lab_type="deadlock-sim",
            event_type="request_resource",
            event_data={
                "process_id": process_id,
                "resource_id": req.resource_id,
                "resource_units": req.units,
                "request_granted": success,
                "process_status": simulator.processes[process_id].status
            }
        )

        return {
            "request_granted": success,
            "process_status": simulator.processes[process_id].status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/processes/{process_id}/release")
def release_resource(process_id: str, req: ResourceReleaseRequest):
    try:
        success = simulator.release_resource(process_id, req.resource_id, req.units)

        send_analytics_event(
            user_id=USER,
            lab_type="deadlock-sim",
            event_type="release_resource",
            event_data={
                "process_id": process_id,
                "resource_id": req.resource_id,
                "resource_units": req.units,
                "release_granted": success,
                "process_status": simulator.processes[process_id].status
            }
        )

        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Deadlock detection endpoints
@app.get("/detect")
def detect_deadlock():
    result = simulator.detect_deadlock()

    send_lab_completion(
        user_id=USER,
        lab_type="deadlock-sim",
        completion_time=len(simulator.processes) + len(simulator.resources),
        success=result['deadlock_detected'],
        errors=[],
        resources_used={i['name']:1 for i in result['deadlocked_processes']}
    )

    return result

# System state endpoints
@app.get("/status")
def get_system_state():
    return simulator.get_system_state()

@app.post("/reset")
def reset_simulator():
    simulator.reset()
    return {"message": "Simulator reset"}