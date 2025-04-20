from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
import json

app = FastAPI(
    title="System Calls API",
    description="API for retrieving system call examples with customizable arguments",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

class SystemCallRequest(BaseModel):
    concept: str = Field(..., example="fork", description="The system call to retrieve")
    arguments: List[str] = Field([], example=["ls", "-l"], description="Arguments for the system call")
    details: str = Field("default", example="default", description="Specific details about the system call")

class SystemCallResponse(BaseModel):
    concept: str = Field(..., example="fork", description="The requested system call")
    code: str = Field(..., example="```c\n#include <stdio.h>\nint main() {}\n```", description="Code example with syntax highlighting")
    explanation: str = Field(..., example="This is an explanation of the system call", description="Detailed explanation of the system call")
    potential_output: str = Field(..., example="Expected output of the code", description="Potential output of the code example")
    required_arguments: List[str] = Field(..., example=["filename", "flags"], description="Required arguments for the system call")
    argument_types: List[str] = Field(..., example=["string", "string"], description="Types of required arguments")
    default_arguments: Optional[List[str]] = Field(None, description="Default arguments for the system call")
    execution_instructions: Dict[str, str]

def load_snippets() -> Dict[str, Dict[str, Any]]:
    try:
        with open("snippets.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Snippets file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON in snippets file")

def format_code_with_arguments(code: str, arguments: List[str], default_args: Optional[List[str]] = None) -> str:
    try:
        # Count the number of format specifiers in the code
        format_count = code.count("%1")
        
        # If no arguments provided, use defaults if available
        if not arguments and default_args:
            arguments = default_args
        
        # Ensure we have enough arguments
        if len(arguments) < format_count:
            raise ValueError(f"Not enough arguments provided. Expected {format_count}, got {len(arguments)}")
        
        # Replace each format specifier with the corresponding argument
        for i in range(1, format_count + 1):
            code = code.replace(f"%{i}", arguments[i-1])
        
        return code
    except Exception as e:
        print(f"Error formatting code: {str(e)}")
        return code  # Return original code if formatting fails

@app.post(
    "/api/system-call",
    response_model=SystemCallResponse,
    summary="Get System Call",
    description="Retrieve a system call example with customizable arguments",
    response_description="System call details with formatted code example"
)
def get_system_call(request: SystemCallRequest):
    snippets = load_snippets()
    
    if request.concept not in snippets:
        raise HTTPException(status_code=404, detail=f"System call '{request.concept}' not found")
    
    if request.details not in snippets[request.concept]:
        raise HTTPException(status_code=404, detail=f"Details '{request.details}' not found for system call '{request.concept}'")
    
    system_call = snippets[request.concept][request.details]
    
    # Format the code with provided arguments
    formatted_code = format_code_with_arguments(
        system_call["code"],
        request.arguments,
        system_call.get("default_arguments")
    )
    
    # Get execution instructions
    exec_instructions = snippets.get("execution_instructions", {}).get("examples", {}).get(request.concept, {})
    
    return SystemCallResponse(
        concept=request.concept,
        code=formatted_code,
        explanation=system_call["explanation"],
        potential_output=system_call["potential_output"],
        required_arguments=system_call["required_arguments"],
        argument_types=system_call["argument_types"],
        default_arguments=system_call.get("default_arguments"),
        execution_instructions={
            "compilation": exec_instructions.get("compilation", "gcc -o program program.c"),
            "execution": exec_instructions.get("execution", "./program"),
            "output_example": exec_instructions.get("output_example", "See potential_output field")
        }
    )

@app.get("/api/system-calls", summary="List Available System Calls")
def list_system_calls():
    """List all available system calls with their descriptions."""
    snippets = load_snippets()
    return {
        "system_calls": {
            name: {
                "description": data["default"]["explanation"],
                "required_arguments": data["default"]["required_arguments"],
                "argument_types": data["default"]["argument_types"]
            }
            for name, data in snippets.items() if name != "execution_instructions"
        }
    }

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to System Calls API. Visit /docs for API documentation."}
