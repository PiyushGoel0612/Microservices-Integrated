from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from scheduler import fcfs, sjf, round_robin
import requests
from urllib.parse import urlencode

app = Flask(__name__)
CORS(app)

# In-memory storage for processes
process_list = []

@app.route("/add", methods=["POST"])
def add_process():
    data = request.json
    process = {
        "pid": data["pid"],
        "arrival_time": data["arrival_time"],
        "burst_time": data["burst_time"],
        "memory_required": data["memory_required"]
    }
    process_list.append(process)

    # Prepare message for shared memory microservice
    message = f"PID={process['pid']},Memory={process['memory_required']}MB"
    try:
        # Send via GET request
        params = urlencode({'message': message})
        memory_url = f"http://ipc-service:8000/simulate/shared_memory/write?{params}"
        response = requests.get(memory_url)
        response.raise_for_status()
    except Exception as e:
        return jsonify({"message": "Process added, but failed to register memory", "error": str(e)}), 207

    return jsonify({"message": "Process added and memory registered"}), 201


@app.route("/simulate", methods=["GET"])
def simulate_scheduler():
    algo = request.args.get("method", "fcfs").lower()

    if algo == "sjf":
        result = sjf(process_list)
    elif algo == "round_robin":
        quantum = int(request.args.get("quantum", 2))
        result = round_robin(process_list, quantum=quantum)
    else:
        result = fcfs(process_list)

    return jsonify(result)

@app.route("/processes", methods=["GET"])
def list_processes():
    return jsonify(process_list)

@app.route("/clear", methods=["POST"])
def clear():
    process_list.clear()
    return jsonify({"message": "All processes cleared"})

@app.route("/")
def serve_ui():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def serve_static_file(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
