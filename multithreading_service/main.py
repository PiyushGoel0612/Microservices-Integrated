import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import models, database, thread_manager

from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])

# ✅ Correct mount for static files like script.js
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.post("/start-task/")
async def start_task(request: Request):
    body = await request.json()
    task_name = body.get("name", "Unnamed Task")

    db = database.SessionLocal()
    task = models.Task(name=task_name, status="Pending")
    db.add(task)
    db.commit()
    db.refresh(task)

    thread_manager.start_thread(task.id)
    db.close()
    return {"task_id": task.id, "message": "Task started"}

@app.get("/tasks/")
def get_tasks():
    db = database.SessionLocal()
    tasks = db.query(models.Task).all()
    db.close()
    return [{"id": t.id, "name": t.name, "status": t.status} for t in tasks]

# ✅ Serve index.html on root
@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

