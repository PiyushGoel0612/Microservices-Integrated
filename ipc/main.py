from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os
from typing import Optional
from pathlib import Path

app = FastAPI()

# Get the absolute path of the current directory
BASE_DIR = Path(__file__).parent.absolute()
IPC_SNIPPETS_DIR = BASE_DIR / "ipc_snippets"

class Message(BaseModel):
    content: str

# Global state to track IPC operations
ipc_state = {
    "shared_memory": {
        "initialized": False,
        "message": None
    },
    "pipe": {
        "initialized": False,
        "message": None
    }
}

def run_binary(binary_path, *args):
    """Helper function to run binaries and handle output"""
    try:
        result = subprocess.run(
            [binary_path] + list(args),
            capture_output=True,
            text=False,  # Don't decode output as text
            timeout=5
        )
        # Decode output manually, replacing invalid characters
        stdout = result.stdout.decode('utf-8', errors='replace').strip()
        stderr = result.stderr.decode('utf-8', errors='replace').strip()
        
        if result.returncode != 0:
            raise Exception(f"Binary execution failed: {stderr}")
            
        return stdout
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Operation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def compile_c_files():
    """Compile C files into binaries when the application starts"""
    try:
        # Compile shared memory program
        shared_mem_src = IPC_SNIPPETS_DIR / "shared_memory.c"
        subprocess.run(["gcc", str(shared_mem_src), "-o", str(shared_mem_src.with_suffix(''))], check=True)
        
        # Compile pipe program
        pipe_src = IPC_SNIPPETS_DIR / "pipe.c"
        subprocess.run(["gcc", str(pipe_src), "-o", str(pipe_src.with_suffix(''))], check=True)
        
        # Make binaries executable
        os.chmod(shared_mem_src.with_suffix(''), 0o755)
        os.chmod(pipe_src.with_suffix(''), 0o755)
        
        print("✅ C files compiled successfully")
    except Exception as e:
        print(f"❌ Error compiling C files: {str(e)}")
        raise

# Compile C files when the application starts
compile_c_files()

@app.get("/")
def read_root():
    return {
        "message": "👋 Welcome to the IPC Simulation API!",
        "instructions": "Use /simulate/{concept}/{action} to perform IPC operations",
        "examples": [
            "/simulate/shared_memory/init",
            "/simulate/shared_memory/write?message=Hello",
            "/simulate/shared_memory/read",
            "/simulate/shared_memory/cleanup"
        ],
        "note": "Supported concepts: shared_memory, pipe"
    }

@app.get("/simulate/shared_memory/{action}")
def simulate_shared_memory(action: str, message: Optional[str] = None):
    binary_path = str(IPC_SNIPPETS_DIR / "shared_memory")
    
    if action == "init":
        if ipc_state["shared_memory"]["initialized"]:
            raise HTTPException(status_code=400, detail="Shared memory already initialized")
        try:
            output = run_binary(binary_path, "init")
            ipc_state["shared_memory"]["initialized"] = True
            return {"status": "success", "message": "Shared memory initialized"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif action == "write":
        if not ipc_state["shared_memory"]["initialized"]:
            raise HTTPException(status_code=400, detail="Shared memory not initialized")
        if not message:
            raise HTTPException(status_code=400, detail="Message parameter required")
        try:
            output = run_binary(binary_path, "write", message)
            ipc_state["shared_memory"]["message"] = message
            return {"status": "success", "message": f"Message written: {message}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif action == "read":
        if not ipc_state["shared_memory"]["initialized"]:
            raise HTTPException(status_code=400, detail="Shared memory not initialized")
        try:
            output = run_binary(binary_path, "read")
            return {"status": "success", "message": f"Message read: {output}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif action == "cleanup":
        try:
            output = run_binary(binary_path, "cleanup")
            ipc_state["shared_memory"]["initialized"] = False
            ipc_state["shared_memory"]["message"] = None
            return {"status": "success", "message": "Shared memory cleaned up"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@app.get("/simulate/pipe/{action}")
def simulate_pipe(action: str, message: Optional[str] = None):
    binary_path = str(IPC_SNIPPETS_DIR / "pipe")
    
    if action == "init":
        if ipc_state["pipe"]["initialized"]:
            raise HTTPException(status_code=400, detail="Pipe already initialized")
        try:
            output = run_binary(binary_path, "init")
            ipc_state["pipe"]["initialized"] = True
            return {"status": "success", "message": "Pipe initialized"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif action == "write":
        if not ipc_state["pipe"]["initialized"]:
            raise HTTPException(status_code=400, detail="Pipe not initialized")
        if not message:
            raise HTTPException(status_code=400, detail="Message parameter required")
        try:
            output = run_binary(binary_path, "write", message)
            ipc_state["pipe"]["message"] = message
            return {"status": "success", "message": f"Message written to pipe: {message}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif action == "read":
        if not ipc_state["pipe"]["initialized"]:
            raise HTTPException(status_code=400, detail="Pipe not initialized")
        try:
            output = run_binary(binary_path, "read")
            return {"status": "success", "message": f"Message read from pipe: {output}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif action == "cleanup":
        try:
            output = run_binary(binary_path, "cleanup")
            ipc_state["pipe"]["initialized"] = False
            ipc_state["pipe"]["message"] = None
            return {"status": "success", "message": "Pipe cleaned up"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail="Invalid action")
