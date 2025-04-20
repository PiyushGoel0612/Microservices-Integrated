document.addEventListener('DOMContentLoaded', () => {
    fetchProcesses();

    document.getElementById('processForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target;

        const data = {
            pid: form.pid.value.trim(),
            arrival_time: parseInt(form.arrival_time.value),
            burst_time: parseInt(form.burst_time.value),
            memory_required: parseInt(form.memory_required.value)
        };

        if (!data.pid || isNaN(data.arrival_time) || isNaN(data.burst_time) || isNaN(data.memory_required)) {
            showMessage('Please fill all required fields correctly.', 'error');
            return;
        }

        try {
            const res = await fetch('/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await res.json();

            form.reset();
            showMessage(result.message || 'Process added successfully!', 'success');
            fetchProcesses();
        } catch (err) {
            showMessage('Failed to add process.', 'error');
        }
    });
});

async function fetchProcesses() {
    try {
        const res = await fetch('/processes');
        const processes = await res.json();
	console.log(processes);

        const tbody = document.querySelector('#processTable tbody');
        tbody.innerHTML = '';

        processes.forEach(p => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${p.pid}</td>
                <td>${p.arrival_time}</td>
                <td>${p.burst_time}</td>
                <td>${p.memory_required !== undefined && p.memory_required !== null ? p.memory_required + ' MB' : '-'}</td>

            `;
            tbody.appendChild(row);
        });
    } catch (err) {
        showMessage('Failed to load processes.', 'error');
    }
}

async function simulate() {
    const loader = document.getElementById('loader');
    loader.style.display = 'block';

    try {
        const res = await fetch('/simulate');
        const result = await res.json();
        document.getElementById('simulationResult').textContent = JSON.stringify(result, null, 2);
        showMessage('Simulation completed.', 'success');
    } catch (err) {
        showMessage('Simulation failed.', 'error');
    } finally {
        loader.style.display = 'none';
    }
}

async function clearAll() {
    try {
        await fetch('/clear', { method: 'POST' });
        document.getElementById('simulationResult').textContent = '';
        fetchProcesses();
        showMessage('All processes cleared.', 'success');
    } catch (err) {
        showMessage('Failed to clear processes.', 'error');
    }
}

function showMessage(msg, type = 'success') {
    const messageBox = document.getElementById('message');
    messageBox.textContent = msg;
    messageBox.className = `message ${type}`;
    setTimeout(() => {
        messageBox.textContent = '';
        messageBox.className = 'message';
    }, 3000);
}


document.getElementById('algorithmSelect').addEventListener('change', () => {
    const selected = document.getElementById('algorithmSelect').value;
    document.getElementById('quantumInput').style.display = selected === 'round_robin' ? 'inline' : 'none';
});

async function simulate() {
    const algo = document.getElementById('algorithmSelect').value;
    const quantum = document.getElementById('quantum').value;

    const loader = document.getElementById('loader');
    loader.style.display = 'block';

    let url = `/simulate?method=${algo}`;
    if (algo === 'round_robin') {
        url += `&quantum=${quantum}`;
    }

    try {
        const res = await fetch(url);
        const result = await res.json();
        document.getElementById('simulationResult').textContent = JSON.stringify(result, null, 2);
        showMessage('Simulation completed.', 'success');
    } catch (err) {
        showMessage('Simulation failed.', 'error');
    } finally {
        loader.style.display = 'none';
    }
}

