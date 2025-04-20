import threading
import time
from database import SessionLocal
from models import Task

def long_running_task(task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    task.status = "Running"
    db.commit()
    
    for i in range(5):  # Simulate work
        print(f"Processing {task_id} - step {i+1}")
        time.sleep(1)

    task.status = "Completed"
    db.commit()
    db.close()

def start_thread(task_id: int):
    thread = threading.Thread(target=long_running_task, args=(task_id,))
    thread.start()

