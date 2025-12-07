import time
import math
import random
import requests
import threading

URL = "http://localhost:8080/stress?intensity=0.4"

def send_request():
    """Envoie une requête"""
    try:
        requests.get(URL, timeout=2)
    except:
        pass

start_time = time.time()

while True:
    elapsed = time.time() - start_time
    
    period = 300
    cycle_position = (elapsed % period) / period 
    
    sine_value = math.sin(2 * math.pi * cycle_position)
    
    base_load = 5
    amplitude = 4
    noise = random.uniform(-1, 2)
    
    concurrency = base_load + (amplitude * sine_value) + noise
    
    concurrency = int(max(0, concurrency))
    
    bar = "█" * concurrency
    print(f"Charge : {concurrency} reqs | {bar}")

    threads = []
    for _ in range(concurrency):
        t = threading.Thread(target=send_request)
        t.start()
        threads.append(t)
        
    time.sleep(1)