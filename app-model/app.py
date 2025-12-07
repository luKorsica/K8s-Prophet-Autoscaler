from flask import Flask, request
import time
import math

app = Flask(__name__)

def burn_cpu(duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        _ = math.sqrt(64 * 64 * 64 * 64 * 64)

@app.route('/')
def health():
    return "Running !", 200

@app.route('/stress')
def stress():
    intensity = request.args.get('intensity', default=0.5, type=float)
    
    burn_cpu(intensity)
    
    return f"CPU brulé pendant {intensity}s 🔥", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)