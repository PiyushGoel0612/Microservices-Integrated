from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import time
import uuid

app = FastAPI()

class File:
    def __init__(self, name: str, content: str = "", parent_dir: str = "/"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.content = content
        self.parent_dir = parent_dir
        self.created_at = time.time()
        self.modified_at = time.time()
        self.size = len(content)
        self.is_locked = False
        self.lock_holder = None

class Directory:
    def __init__(self, name: str, parent_dir: str = "/"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.parent_dir = parent_dir
        self.created_at = time.time()
        self.modified_at = time.time()

class FileSystemManager:
    def __init__(self):
        self.files = {}  # id -> File
        self.directories = {}  # id -> Directory
        
        # Create root directory
        root = Directory("/", "")
        self.directories[root.id] = root
        
    def create_file(self, name: str, content: str, parent_dir: str) -> File:
        # Check if parent directory exists
        parent_exists = any(d.name == parent_dir for d in self.directories.values())
        if not parent_exists:
            raise ValueError(f"Parent directory {parent_dir} does not exist")
            
        # Check if file already exists in this directory
        if any(f.name == name and f.parent_dir == parent_dir for f in self.files.values()):
            raise ValueError(f"File {name} already exists in {parent_dir}")
            
        file = File(name, content, parent_dir)
        self.files[file.id] = file
        return file
    
    def read_file(self, file_id: str) -> str:
        if file_id not in self.files:
            raise ValueError(f"File with id {file_id} not found")
        
        file = self.files[file_id]
        if file.is_locked:
            raise ValueError(f"File {file.name} is locked by another process")
            
        return file.content
    
    def write_file(self, file_id: str, content: str) -> File:
        if file_id not in self.files:
            raise ValueError(f"File with id {file_id} not found")
            
        file = self.files[file_id]
        if file.is_locked and file.lock_holder != "current_user":
            raise ValueError(f"File {file.name} is locked by another process")
            
        file.content = content
        file.modified_at = time.time()
        file.size = len(content)
        return file
    
    def delete_file(self, file_id: str) -> bool:
        if file_id not in self.files:
            raise ValueError(f"File with id {file_id} not found")
            
        file = self.files[file_id]
        if file.is_locked:
            raise ValueError(f"File {file.name} is locked by another process")
            
        del self.files[file_id]
        return True
    
    def create_directory(self, name: str, parent_dir: str) -> Directory:
        # Check if parent directory exists
        parent_exists = any(d.name == parent_dir for d in self.directories.values())
        if not parent_exists:
            raise ValueError(f"Parent directory {parent_dir} does not exist")
            
        # Check if directory already exists in this parent
        if any(d.name == name and d.parent_dir == parent_dir for d in self.directories.values()):
            raise ValueError(f"Directory {name} already exists in {parent_dir}")
            
        directory = Directory(name, parent_dir)
        self.directories[directory.id] = directory
        return directory
    
    def list_directory(self, dir_path: str) -> dict:
        files = [f for f in self.files.values() if f.parent_dir == dir_path]
        dirs = [d for d in self.directories.values() if d.parent_dir == dir_path]
        
        return {
            "files": [{"id": f.id, "name": f.name, "size": f.size, 
                      "created_at": f.created_at, "modified_at": f.modified_at} 
                     for f in files],
            "directories": [{"id": d.id, "name": d.name, 
                            "created_at": d.created_at} 
                           for d in dirs]
        }
    
    def lock_file(self, file_id: str, user_id: str) -> bool:
        if file_id not in self.files:
            raise ValueError(f"File with id {file_id} not found")
            
        file = self.files[file_id]
        if file.is_locked:
            return False
            
        file.is_locked = True
        file.lock_holder = user_id
        return True
    
    def unlock_file(self, file_id: str, user_id: str) -> bool:
        if file_id not in self.files:
            raise ValueError(f"File with id {file_id} not found")
            
        file = self.files[file_id]
        if not file.is_locked or file.lock_holder != user_id:
            return False
            
        file.is_locked = False
        file.lock_holder = None
        return True

# Initialize file system
fs_manager = FileSystemManager()

# Request models
class FileRequest(BaseModel):
    name: str
    content: str = ""
    parent_dir: str = "/"

class DirectoryRequest(BaseModel):
    name: str
    parent_dir: str = "/"

class WriteRequest(BaseModel):
    content: str

class LockRequest(BaseModel):
    user_id: str


@app.get("/")
def root():
    return {"message": "Hello from filesystem!"}

# File endpoints
@app.post("/files/")
def create_file(req: FileRequest):
    try:
        file = fs_manager.create_file(req.name, req.content, req.parent_dir)
        return {
            "id": file.id,
            "name": file.name,
            "size": file.size,
            "created_at": file.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/files/{file_id}")
def read_file(file_id: str):
    try:
        content = fs_manager.read_file(file_id)
        file = fs_manager.files[file_id]
        return {
            "id": file.id,
            "name": file.name,
            "content": content,
            "size": file.size,
            "created_at": file.created_at,
            "modified_at": file.modified_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/files/{file_id}")
def write_file(file_id: str, req: WriteRequest):
    try:
        file = fs_manager.write_file(file_id, req.content)
        return {
            "id": file.id,
            "name": file.name,
            "size": file.size,
            "modified_at": file.modified_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/files/{file_id}")
def delete_file(file_id: str):
    try:
        success = fs_manager.delete_file(file_id)
        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/files/{file_id}/lock")
def lock_file(file_id: str, req: LockRequest):
    try:
        success = fs_manager.lock_file(file_id, req.user_id)
        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/files/{file_id}/unlock")
def unlock_file(file_id: str, req: LockRequest):
    try:
        success = fs_manager.unlock_file(file_id, req.user_id)
        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Directory endpoints
@app.post("/directories/")
def create_directory(req: DirectoryRequest):
    try:
        directory = fs_manager.create_directory(req.name, req.parent_dir)
        return {
            "id": directory.id,
            "name": directory.name,
            "created_at": directory.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/directories/{dir_path}")
def list_directory(dir_path: str):
    try:
        contents = fs_manager.list_directory(dir_path)
        return contents
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))