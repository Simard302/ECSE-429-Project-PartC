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

        start_time = time.time()
        initial_cpu_times = psutil_process.cpu_times()
        mem_values_create = []
        cpu_values_create = []
        time_values_create = []

        for i in range(1, 10000+1):
            response = session.post('http://localhost:8080/todos', json={
                "title": "a"*1000,          # 1KB
                "doneStatus": False,
                "description": "b"*1000,    # 1KB
            })
            if response.status_code != 201:
                print(f'Error at {i} code: {response.status_code}')
                break
            
            if i % 100 == 0:
                mem_usage = psutil_process.memory_info().rss / (1024 * 1024)
                mem_values_create.append((i, mem_usage))

                timestamp = time.time() - start_time
                time_values_create.append((i, timestamp))

                final_cpu_times = psutil_process.cpu_times()
                cpu_usage = diff_cpu_times(initial_cpu_times, final_cpu_times)
                cpu_values_create.append((i, cpu_usage))
                print(f'Created {i} todos')
                print(f'Memory usage: {mem_usage} MB')
                print(f'CPU time: {cpu_usage} seconds')
                print(f'Time elapsed: {timestamp} seconds')
        
        start_time = time.time()
        initial_cpu_times = psutil_process.cpu_times()
        mem_values_delete = []
        cpu_values_delete = []
        time_values_delete = []

        for i in range(1, 10000+1):
            response = session.delete(f'http://localhost:8080/todos/{i}')
            if response.status_code != 200:
                print(f'Error at {i} code: {response.status_code}')
                break
            if i % 100 == 0:
                mem_usage = psutil_process.memory_info().rss / (1024 * 1024)
                mem_values_delete.append((i, mem_usage))

                timestamp = time.time() - start_time
                time_values_delete.append((i, timestamp))

                final_cpu_times = psutil_process.cpu_times()
                cpu_usage = diff_cpu_times(initial_cpu_times, final_cpu_times)
                cpu_values_delete.append((i, cpu_usage))
                print(f'Deleted {i} todos')
                print(f'Memory usage: {mem_usage} MB')
                print(f'CPU time: {cpu_usage} seconds')
                print(f'Time elapsed: {timestamp} seconds')

    x_mem, y_mem = zip(*mem_values_create)
    x_cpu, y_cpu = zip(*cpu_values_create)
    x_time, y_time = zip(*time_values_create)
    
    plt.figure(figsize=(18, 6))
    plt.subplot(1, 3, 1)
    plt.plot(x_mem, y_mem, marker='o')
    plt.title('Memory Usage over Todos Created')
    plt.xlabel('Number of Todos Created')
    plt.ylabel('Total Memory Usage (MB)')
    plt.grid(True)

    plt.subplot(1, 3, 2)
    plt.plot(x_cpu, y_cpu, marker='o', color='red')
    plt.title('CPU Usage over Todos Created')
    plt.xlabel('Number of Todos Created')
    plt.ylabel('Total Time Spent in CPU (Seconds)')
    plt.grid(True)

    plt.subplot(1, 3, 3)
    plt.plot(x_time, y_time, marker='o', color='orange')
    plt.title('Time Elapsed over Todos Created')
    plt.xlabel('Number of Todos Created')
    plt.ylabel('Total Time Elapsed (Seconds)')
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('part3/create_performance.png')
    plt.close()

    x_mem, y_mem = zip(*mem_values_delete)
    x_cpu, y_cpu = zip(*cpu_values_delete)
    x_time, y_time = zip(*time_values_delete)

    plt.figure(figsize=(18, 6))
    plt.subplot(1, 3, 1)
    plt.plot(x_mem, y_mem, marker='o')
    plt.title('Memory Usage over Todos Deleted')
    plt.xlabel('Number of Todos Deleted')
    plt.ylabel('Memory Usage (MB)')
    plt.grid(True)

    plt.subplot(1, 3, 2)
    plt.plot(x_cpu, y_cpu, marker='o', color='red')
    plt.title('CPU Usage over Todos Deleted')
    plt.xlabel('Number of Todos Deleted')
    plt.ylabel('CPU Usage (%)')
    plt.grid(True)

    plt.subplot(1, 3, 3)
    plt.plot(x_time, y_time, marker='o', color='orange')
    plt.title('Time Elapsed over Todos Deleted')
    plt.xlabel('Number of Todos Deleted')
    plt.ylabel('Time Elapsed (Seconds)')
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('part3/delete_performance.png')

finally:
    process.terminate()
    process.wait()