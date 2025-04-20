async function startTask() {
  const name = document.getElementById("taskName").value;
  await fetch("http://localhost:8000/start-task/", {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  });
  loadTasks();
}

async function loadTasks() {
  const response = await fetch("http://localhost:8000/tasks/");
  const tasks = await response.json();

  const listDiv = document.getElementById("taskList");
  listDiv.innerHTML = tasks.map(t => 
    `<div class="border-b py-2">${t.name} - <strong>${t.status}</strong></div>`
  ).join('');
}

setInterval(loadTasks, 2000); // Auto-refresh every 2s

