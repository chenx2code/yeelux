from flask import Flask, jsonify, request, render_template
import sys
import os
import json
import logging
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from light_controller import LightManager
from scheduler import LightScheduler

# Load .env variables
load_dotenv()

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

# Load devices from devices.json
devices_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'devices.json')
try:
    with open(devices_file, 'r', encoding='utf-8') as f:
        devices_config = json.load(f)
except Exception as e:
    raise ValueError(f"Failed to read devices.json config file: {e}")

managers = {}
schedulers = {}

for dev in devices_config:
    dev_id = dev['id']
    managers[dev_id] = LightManager(dev['ip'], dev['token'], dev.get('name', 'Unknown Light'))
    schedulers[dev_id] = LightScheduler(managers[dev_id])

@app.route('/')
def index():
    return render_template('index.html', devices=devices_config)

@app.route('/api/status/all', methods=['GET'])
def get_all_status():
    result = {}
    for dev_id, light in managers.items():
        status = light.get_status()
        if status:
            result[dev_id] = {
                'success': True,
                'is_on': status.is_on,
                'brightness': status.brightness,
                'color_temp': status.color_temp if hasattr(status, 'color_temp') else 4000
            }
        else:
            result[dev_id] = {'success': False, 'error': 'Disconnected'}
    return jsonify(result)

@app.route('/api/status/<device_id>', methods=['GET'])
def get_status(device_id):
    if device_id not in managers:
        return jsonify({'success': False, 'error': 'Device not found'})
    status = managers[device_id].get_status()
    if status:
        return jsonify({
            'success': True,
            'is_on': status.is_on,
            'brightness': status.brightness,
            'color_temp': status.color_temp if hasattr(status, 'color_temp') else 4000
        })
    return jsonify({'success': False, 'error': 'Disconnected'})

@app.route('/api/toggle/<device_id>', methods=['POST'])
def toggle(device_id):
    if device_id not in managers:
        return jsonify({'success': False, 'error': 'Device not found'})
    managers[device_id].toggle()
    return get_status(device_id)

@app.route('/api/brightness/<device_id>', methods=['POST'])
def set_brightness(device_id):
    if device_id not in managers:
        return jsonify({'success': False, 'error': 'Device not found'})
    data = request.json
    val = data.get('value', 50)
    managers[device_id].set_brightness(int(val))
    return jsonify({'success': True})

@app.route('/api/colortemp/<device_id>', methods=['POST'])
def set_colortemp(device_id):
    if device_id not in managers:
        return jsonify({'success': False, 'error': 'Device not found'})
    data = request.json
    val = data.get('value', 4000)
    managers[device_id].set_color_temp(int(val))
    return jsonify({'success': True})

@app.route('/api/timer/<device_id>', methods=['GET', 'POST'])
def handle_timer(device_id):
    if device_id not in schedulers:
        return jsonify({'success': False, 'error': 'Device not found'})
    scheduler = schedulers[device_id]
    if request.method == 'POST':
        data = request.json
        if data.get('action') == 'start':
            mins = int(data.get('minutes', 15))
            scheduler.start_timer(mins)
        elif data.get('action') == 'stop':
            scheduler.stop_timer()
        return jsonify({'success': True})
    else:
        return jsonify(scheduler.get_timer_status())

@app.route('/api/focus/<device_id>', methods=['GET', 'POST'])
def handle_focus(device_id):
    if device_id not in schedulers:
        return jsonify({'success': False, 'error': 'Device not found'})
    scheduler = schedulers[device_id]
    if request.method == 'POST':
        data = request.json
        if data.get('action') == 'start':
            work_mins = int(data.get('work_mins', 45))
            rest_mins = int(data.get('rest_mins', 10))
            scheduler.start_focus(work_mins, rest_mins)
        elif data.get('action') == 'stop':
            scheduler.stop_focus()
        return jsonify({'success': True})
    else:
        return jsonify(scheduler.get_focus_status())

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
