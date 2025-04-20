from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

TOTAL_MEMORY = 4096
PAGE_SIZE = 4

# In-memory allocation list
allocations = []

def get_used_memory():
    return sum(a['memory'] for a in allocations if not a['swapped'])

class ProcessAllocation(BaseModel):
    process_id: str
    memory: int

@app.get("/")
def index():
    return {"message": "Memory Manager Service"}

@app.post("/allocate")
def allocate(process: ProcessAllocation):
    used_memory = get_used_memory()
    pages = (process.memory + PAGE_SIZE - 1) // PAGE_SIZE
    swapped = used_memory + process.memory > TOTAL_MEMORY

    allocations.append({
        "process_id": process.process_id,
        "memory": process.memory,
        "pages": pages,
        "swapped": swapped
    })

    return JSONResponse(
        content={"message": f"{'Swapped' if swapped else 'Allocated'} {process.memory}MB to {process.process_id}"}
    )

@app.post("/deallocate")
def deallocate(process: ProcessAllocation):
    for i, alloc in enumerate(allocations):
        if alloc['process_id'] == process.process_id:
            memory = alloc['memory']
            del allocations[i]
            return JSONResponse(
                content={"message": f"Deallocated {memory}MB from {process.process_id}"}
            )

    raise HTTPException(status_code=404, detail="Process not found")

@app.get("/status")
def status():
    used_memory = get_used_memory()
    return {
        "total_memory": TOTAL_MEMORY,
        "used_memory": used_memory,
        "free_memory": TOTAL_MEMORY - used_memory,
        "allocations": allocations
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8000)