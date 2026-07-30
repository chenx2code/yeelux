import sys
import os
import json
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, send_from_directory
import uuid

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

@app.route('/service-worker.js')
def serve_sw():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/favicon.png')
def serve_favicon():
    return send_from_directory('static/images', 'favicon.png', mimetype='image/png')

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

PRESETS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'presets.json')

def load_presets():
    if not os.path.exists(PRESETS_FILE):
        default_presets = [
            {"id": "preset_rest", "brightness": 10, "color_temp": 2600},
            {"id": "preset_work", "brightness": 100, "color_temp": 4200}
        ]
        save_presets(default_presets)
        return default_presets
    try:
        with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_presets(presets):
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, indent=4)

@app.route('/api/presets', methods=['GET'])
def get_presets():
    return jsonify(load_presets())

@app.route('/api/presets', methods=['POST'])
def save_preset():
    data = request.json
    presets = load_presets()
    preset_id = data.get('id')
    
    if preset_id:
        for p in presets:
            if p['id'] == preset_id:
                if 'name' in data: p['name'] = data['name']
                p['brightness'] = int(data.get('brightness', 50))
                p['color_temp'] = int(data.get('color_temp', 4000))
                break
        else:
            presets.append({
                "id": preset_id,
                "name": data.get('name', ''),
                "brightness": int(data.get('brightness', 50)),
                "color_temp": int(data.get('color_temp', 4000))
            })
        saved_id = preset_id
    else:
        saved_id = "preset_" + str(uuid.uuid4())[:8]
        presets.append({
            "id": saved_id,
            "name": data.get('name', ''),
            "brightness": int(data.get('brightness', 50)),
            "color_temp": int(data.get('color_temp', 4000))
        })
    
    save_presets(presets)
    return jsonify({'success': True, 'presets': presets, 'id': saved_id})

@app.route('/api/presets/<preset_id>', methods=['DELETE'])
def delete_preset(preset_id):
    presets = load_presets()
    presets = [p for p in presets if p['id'] != preset_id]
    save_presets(presets)
    return jsonify({'success': True, 'presets': presets})

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
            rest_action = data.get('rest_action', 'dim')
            rest_brightness = int(data.get('rest_brightness', 5))
            rest_color_temp = int(data.get('rest_color_temp', 2700))
            scheduler.start_focus(work_mins, rest_mins, rest_action, rest_brightness, rest_color_temp)
        elif data.get('action') == 'stop':
            scheduler.stop_focus()
        return jsonify({'success': True})
    else:
        return jsonify(scheduler.get_focus_status())



if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    is_debug = os.getenv("FLASK_DEBUG", "false").lower() in ["true", "1", "t", "yes"]
    
    app.run(host='0.0.0.0', port=port, debug=is_debug)
