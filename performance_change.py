import matplotlib.pyplot as plt
import subprocess
import time
import requests
import psutil


def start_jar_in_background():
    process = subprocess.Popen(
        ['java', '-jar', 'part3/runTodoManagerRestAPI-1.5.5.jar', '-port=8080'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1   # line buffered
    )
    return process

def wait_for_server_to_start(process: subprocess.Popen[str]):
    printed_lines = 0
    for line in process.stdout:
        print(line.strip(), printed_lines)
        printed_lines += 1
        if printed_lines >= 12:
            time.sleep(0.1)
            return

def diff_cpu_times(initial_cpu_times, final_cpu_times):
    user_time = final_cpu_times.user - initial_cpu_times.user
    system_time = final_cpu_times.system - initial_cpu_times.system
    return user_time + system_time

process = start_jar_in_background()

try:
    wait_for_server_to_start(process)
    psutil_process = psutil.Process(process.pid)

    with requests.Session() as session:

        mem_values_change = []
        cpu_values_change = []
        time_values_change = []

        for i in range(1, 10000+1):
            response = session.post('http://localhost:8080/todos', json={
                "title": "a"*1000,          # 1KB
                "doneStatus": False,
                "description": "a"*1000,    # 1KB
            })
            if response.status_code != 201:
                print(f'Error at {i} code: {response.status_code}')
                break
            

            if i % 1000 == 0:
                start_time = time.time()
                initial_cpu_times = psutil_process.cpu_times()
                for j in range(1, i+1):
                    response = session.put(f'http://localhost:8080/todos/{j}', json={
                        "title": "a"*1000,          # 1KB
                        "doneStatus": False,
                        "description": "a"*1000,    # 1KB
                    })
                mem_usage = psutil_process.memory_info().rss / (1024 * 1024)
                mem_values_change.append((i, mem_usage))
                
                timestamp = time.time() - start_time
                time_values_change.append((i, timestamp))

                final_cpu_times = psutil_process.cpu_times()
                cpu_usage = diff_cpu_times(initial_cpu_times, final_cpu_times)
                cpu_values_change.append((i, cpu_usage))
                print(f'Changed {i} todos')
                print(f'Memory usage: {mem_usage} MB')
                print(f'CPU time: {cpu_usage} seconds')
                print(f'Time elapsed: {timestamp} seconds')

    x_mem, y_mem = zip(*mem_values_change)
    x_cpu, y_cpu = zip(*cpu_values_change)
    x_time, y_time = zip(*time_values_change)
    
    plt.figure(figsize=(18, 6))
    plt.subplot(1, 3, 1)
    plt.plot(x_mem, y_mem, marker='o')
    plt.title('Memory Usage over Todos Changed')
    plt.xlabel('Number of Todos Changed')
    plt.ylabel('Memory Usage (MB)')
    plt.grid(True)

    plt.subplot(1, 3, 2)
    plt.plot(x_cpu, y_cpu, marker='o', color='green')
    plt.title('CPU Usage over Todos Changed')
    plt.xlabel('Number of Todos Changed')
    plt.ylabel('Time Spent in CPU (Seconds)')
    plt.grid(True)

    plt.subplot(1, 3, 3)
    plt.plot(x_time, y_time, marker='o', color='orange')
    plt.title('Time Elapsed over Todos Changed')
    plt.xlabel('Number of Todos Changed')
    plt.ylabel('Time Elapsed (Seconds)')
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('part3/change_performance.png')
    plt.close()

finally:
    process.terminate()
    process.wait()