from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

TOTAL_MEMORY = 4096
PAGE_SIZE = 4

# In-memory allocation list
allocations = []

def get_used_memory():
    return sum(a['memory'] for a in allocations if not a['swapped'])

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/allocate", methods=["POST"])
def allocate():
    data = request.json
    process_id = data.get("process_id")
    memory = data.get("memory")

    if not process_id or memory is None:
        return jsonify({"error": "Missing 'process_id' or 'memory'"}), 400

    # Ensure memory is an integer
    try:
        memory = int(memory)
    except ValueError:
        return jsonify({"error": "'memory' must be an integer"}), 400

    used_memory = get_used_memory()
    pages = (memory + PAGE_SIZE - 1) // PAGE_SIZE
    swapped = used_memory + memory > TOTAL_MEMORY

    allocations.append({
        "process_id": process_id,
        "memory": memory,
        "pages": pages,
        "swapped": swapped
    })

    return jsonify({
        "message": f"{'Swapped' if swapped else 'Allocated'} {memory}MB to {process_id}"
    })

@app.route("/deallocate", methods=["POST"])
def deallocate():
    data = request.json
    process_id = data.get("process_id")

    if not process_id:
        return jsonify({"error": "Missing 'process_id'"}), 400

    for i, alloc in enumerate(allocations):
        if alloc['process_id'] == process_id:
            memory = alloc['memory']
            del allocations[i]
            return jsonify({
                "message": f"Deallocated {memory}MB from {process_id}"
            })

    return jsonify({"error": "Process not found"}), 404

@app.route("/status", methods=["GET"])
def status():
    used_memory = get_used_memory()
    return jsonify({
        "total_memory": TOTAL_MEMORY,
        "used_memory": used_memory,
        "free_memory": TOTAL_MEMORY - used_memory,
        "allocations": allocations
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)