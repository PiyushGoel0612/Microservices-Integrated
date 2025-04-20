def fcfs(processes):
    processes.sort(key=lambda x: x['arrival_time'])
    time = 0
    result = []

    for p in processes:
        start_time = max(time, p['arrival_time'])
        finish_time = start_time + p['burst_time']
        waiting_time = start_time - p['arrival_time']
        turnaround_time = finish_time - p['arrival_time']

        result.append({
            'pid': p['pid'],
            'start_time': start_time,
            'finish_time': finish_time,
            'waiting_time': waiting_time,
            'turnaround_time': turnaround_time
        })

        time = finish_time

    return result


# scheduler.py

def sjf(processes):
    time = 0
    result = []
    completed = []
    ready_queue = []

    processes = sorted(processes, key=lambda x: x['arrival_time'])  # Sort by arrival initially

    while len(completed) < len(processes):
        # Add available processes to the ready queue
        for p in processes:
            if p['arrival_time'] <= time and p not in completed and p not in ready_queue:
                ready_queue.append(p)

        if ready_queue:
            # Pick the shortest job
            ready_queue.sort(key=lambda x: x['burst_time'])
            current = ready_queue.pop(0)

            start_time = max(time, current['arrival_time'])
            finish_time = start_time + current['burst_time']
            waiting_time = start_time - current['arrival_time']
            turnaround_time = finish_time - current['arrival_time']

            result.append({
                'pid': current['pid'],
                'start_time': start_time,
                'finish_time': finish_time,
                'waiting_time': waiting_time,
                'turnaround_time': turnaround_time
            })

            time = finish_time
            completed.append(current)
        else:
            # If no processes have arrived yet, just move forward in time
            time += 1

    return result


def round_robin(processes, quantum=2):
    queue = sorted(processes, key=lambda x: x['arrival_time'])
    result = []
    time = 0
    index = 0
    remaining_bt = {p['pid']: p['burst_time'] for p in processes}
    last_time = {p['pid']: 0 for p in processes}
    visited = set()
    completed = set()

    while queue:
        p = queue[index]
        pid = p['pid']
        if remaining_bt[pid] > 0:
            start_time = max(time, p['arrival_time'])
            exec_time = min(quantum, remaining_bt[pid])
            time = start_time + exec_time
            remaining_bt[pid] -= exec_time

            if pid not in visited:
                visited.add(pid)
                result.append({
                    'pid': pid,
                    'start_time': start_time,
                    'burst_time': p['burst_time'],
                    'waiting_time': 0,  # Will update later
                    'turnaround_time': 0  # Will update later
                })

            if remaining_bt[pid] == 0:
                completed.add(pid)
                for r in result:
                    if r['pid'] == pid:
                        r['finish_time'] = time
                        r['waiting_time'] = time - p['arrival_time'] - p['burst_time']
                        r['turnaround_time'] = time - p['arrival_time']

        index = (index + 1) % len(queue)
        if all(remaining_bt[pid] == 0 for pid in remaining_bt):
            break

    return result
