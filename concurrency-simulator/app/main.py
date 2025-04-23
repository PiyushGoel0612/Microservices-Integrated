from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional
import threading
import uuid
from enum import Enum
import time

app = FastAPI()

class SimulationStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"

class SimulationType(str, Enum):
    PRODUCER_CONSUMER = "producer_consumer"
    DINING_PHILOSOPHERS = "dining_philosophers"

simulations: Dict[str, "BaseSimulation"] = {}

class BaseSimulation:
    def __init__(self, sim_type: SimulationType):
        self.sim_type = sim_type
        self.status = SimulationStatus.READY
        self.log = []
        self.threads = []
    
    def start(self):
        self.status = SimulationStatus.RUNNING
    
    def pause(self):
        self.status = SimulationStatus.PAUSED
    
    def resume(self):
        self.status = SimulationStatus.RUNNING
    
    def stop(self):
        self.status = SimulationStatus.COMPLETED
        for thread in self.threads:
            thread.join(timeout=1.0)
    
    def get_state(self):
        return {"type": self.sim_type, "status": self.status, "log": self.log[-20:]}

class ProducerConsumerSimulation(BaseSimulation):
    def __init__(self, buffer_size: int = 5, producer_time: float = 1.0, consumer_time: float = 1.0):
        super().__init__(SimulationType.PRODUCER_CONSUMER)
        self.buffer = []
        self.buffer_size = buffer_size
        self.lock = threading.Lock()
        self.producer_time = producer_time
        self.consumer_time = consumer_time

    def producer(self):
        while self.status == SimulationStatus.RUNNING:
            with self.lock:
                if len(self.buffer) < self.buffer_size:
                    self.buffer.append("Item")
                    self.log.append("Produced an item")
            threading.Event().wait(self.producer_time)

    def consumer(self):
        while self.status == SimulationStatus.RUNNING:
            with self.lock:
                if self.buffer:
                    self.buffer.pop(0)
                    self.log.append("Consumed an item")
            threading.Event().wait(self.consumer_time)
    
    def start(self):
        super().start()
        self.threads = [threading.Thread(target=self.producer), threading.Thread(target=self.consumer)]
        for t in self.threads:
            t.start()

class DiningPhilosophersSimulation(BaseSimulation):
    def __init__(self, num_philosophers: int = 5, thinking_time: float = 1.0, eating_time: float = 1.0):
        super().__init__(SimulationType.DINING_PHILOSOPHERS)
        self.num_philosophers = num_philosophers
        self.thinking_time = thinking_time
        self.eating_time = eating_time
        self.forks = [threading.Lock() for _ in range(num_philosophers)]
        self.states = ["Thinking"] * num_philosophers
        self.state_lock = threading.Lock()
        self._running_flag = threading.Event()
        self._running_flag.set()
        self._pause_flag = threading.Event()
        self._pause_flag.set()  # Not paused initially
    
    def _initialize_threads(self):
        self.threads = [
            threading.Thread(target=self.philosopher_task, args=(i,))
            for i in range(self.num_philosophers)
        ]
    
    def should_continue(self):
        return self.status in [SimulationStatus.RUNNING, SimulationStatus.PAUSED]
    
    def wait_if_paused(self):
        if self.status == SimulationStatus.PAUSED:
            self._pause_flag.wait()  # Wait until unpaused
    
    def start(self):
        super().start()
        self._initialize_threads()
        self._running_flag.set()
        self._pause_flag.set()
        for thread in self.threads:
            thread.start()
    
    def pause(self):
        super().pause()
        self._pause_flag.clear()  # Signal threads to pause
    
    def resume(self):
        super().resume()
        self._pause_flag.set()  # Signal threads to resume
    
    def stop(self):
        self._running_flag.clear()  # Signal threads to stop
        super().stop()
    
    def philosopher_task(self, philosopher_id: int):
        left_fork = philosopher_id
        right_fork = (philosopher_id + 1) % self.num_philosophers
        
        # To prevent deadlock, even philosophers pick right fork first, odd pick left fork first
        if philosopher_id % 2 == 0:
            first_fork, second_fork = right_fork, left_fork
        else:
            first_fork, second_fork = left_fork, right_fork
        
        while self.should_continue():
            self.wait_if_paused()
            
            # Thinking
            with self.state_lock:
                self.states[philosopher_id] = "Thinking"
                self.log.append(f"Philosopher {philosopher_id} is thinking")
            
            time.sleep(self.thinking_time)
            self.wait_if_paused()
            
            # Try to pick up first fork
            self.forks[first_fork].acquire()
            with self.state_lock:
                self.log.append(f"Philosopher {philosopher_id} picked up fork {first_fork}")
            
            self.wait_if_paused()
            
            # Try to pick up second fork
            acquired = self.forks[second_fork].acquire(timeout=2)  # Prevent deadlock with timeout
            if acquired:
                with self.state_lock:
                    self.states[philosopher_id] = "Eating"
                    self.log.append(f"Philosopher {philosopher_id} picked up fork {second_fork} and is eating")
                
                time.sleep(self.eating_time)
                
                # Put down both forks
                self.forks[second_fork].release()
                with self.state_lock:
                    self.log.append(f"Philosopher {philosopher_id} put down fork {second_fork}")
            else:
                # Handle timeout case
                with self.state_lock:
                    self.log.append(f"Philosopher {philosopher_id} couldn't get fork {second_fork}, putting down fork {first_fork}")
            
            self.forks[first_fork].release()
            with self.state_lock:
                self.log.append(f"Philosopher {philosopher_id} put down fork {first_fork}")
    
    def get_state(self):
        base_state = super().get_state()
        base_state["philosophers"] = self.states
        return base_state

class CreateSimulationRequest(BaseModel):
    sim_type: SimulationType
    buffer_size: Optional[int] = 5
    producer_time: Optional[float] = 1.0
    consumer_time: Optional[float] = 1.0
    num_philosophers: Optional[int] = 5
    thinking_time: Optional[float] = 1.0
    eating_time: Optional[float] = 1.0

@app.post("/simulations/")
def create_simulation(request: CreateSimulationRequest):
    sim_id = str(uuid.uuid4())
    if request.sim_type == SimulationType.PRODUCER_CONSUMER:
        simulations[sim_id] = ProducerConsumerSimulation(
            buffer_size=request.buffer_size,
            producer_time=request.producer_time,
            consumer_time=request.consumer_time
        )
    elif request.sim_type == SimulationType.DINING_PHILOSOPHERS:
        simulations[sim_id] = DiningPhilosophersSimulation(
            num_philosophers=request.num_philosophers,
            thinking_time=request.thinking_time,
            eating_time=request.eating_time
        )
    return {"sim_id": sim_id, "status": simulations[sim_id].status}

@app.get("/simulations/")
def list_simulations():
    return {"simulations": list(simulations.keys())}

@app.post("/simulations/{sim_id}/start")
def start_simulation(sim_id: str):
    if sim_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    simulations[sim_id].start()
    return {"status": simulations[sim_id].status}

@app.post("/simulations/{sim_id}/pause")
def pause_simulation(sim_id: str):
    if sim_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    simulations[sim_id].pause()
    return {"status": simulations[sim_id].status}

@app.post("/simulations/{sim_id}/resume")
def resume_simulation(sim_id: str):
    if sim_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    simulations[sim_id].resume()
    return {"status": simulations[sim_id].status}

@app.post("/simulations/{sim_id}/stop")
def stop_simulation(sim_id: str):
    if sim_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    simulations[sim_id].stop()
    return {"status": simulations[sim_id].status}

@app.get("/simulations/{sim_id}/status")
def get_simulation_status(sim_id: str):
    if sim_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulations[sim_id].get_state()
