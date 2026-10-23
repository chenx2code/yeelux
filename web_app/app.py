import sys
import os
import json
import logging
import tempfile
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, send_from_directory
import uuid
import threading
import time

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

TIMER_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'timer_settings.json')

def get_device_timer_config(settings, dev_id):
    val = settings.get(dev_id, 15)
    if isinstance(val, dict):
        mins = int(val.get('minutes', 15))
        restore = bool(val.get('restore_work_mode', True))
        pending = bool(val.get('pending_restore', False))
    else:
        mins = int(val) if val else 15
        restore = True
        pending = False
    return {'minutes': mins, 'restore_work_mode': restore, 'pending_restore': pending}

def load_timer_settings():
    if not os.path.exists(TIMER_SETTINGS_FILE):
        example_file = TIMER_SETTINGS_FILE.replace('timer_settings.json', 'timer_settings.example.json')
        try:
            with open(example_file, 'r', encoding='utf-8') as f:
                default_settings = json.load(f)
        except Exception:
            default_settings = {}
        save_timer_settings(default_settings)
        return default_settings
    try:
        with open(TIMER_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_timer_settings(settings):
    try:
        dir_name = os.path.dirname(TIMER_SETTINGS_FILE)
        fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix='timer_settings_', suffix='.tmp')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        os.replace(temp_path, TIMER_SETTINGS_FILE)
    except Exception as e:
        logging.error(f"Failed to save timer_settings.json: {e}")

managers = {}
schedulers = {}

initial_timer_settings = load_timer_settings()

def make_on_timer_end(d_id):
    def callback():
        settings = load_timer_settings()
        cfg = get_device_timer_config(settings, d_id)
        cfg['pending_restore'] = True
        settings[d_id] = cfg
        save_timer_settings(settings)
        logging.info(f"[{d_id}] Sleep timer ended: pending_restore set to True in timer_settings.json")
    return callback

for dev in devices_config:
    dev_id = dev['id']
    managers[dev_id] = LightManager(dev['ip'], dev['token'], dev.get('name', 'Unknown Light'))
    cfg = get_device_timer_config(initial_timer_settings, dev_id)
    schedulers[dev_id] = LightScheduler(
        managers[dev_id],
        timer_mins=cfg['minutes'],
        restore_work_mode=cfg['restore_work_mode'],
        on_timer_end=make_on_timer_end(dev_id)
    )

status_cache = {}
last_action_time = {}
last_power_state = {}

def poll_device_status():
    # Initial quick poll
    for dev_id, light in managers.items():
        status = light.get_status()
        if status:
            last_power_state[dev_id] = status.is_on
            status_cache[dev_id] = {
                'success': True,
                'is_on': status.is_on,
                'brightness': status.brightness,
                'color_temp': status.color_temp if hasattr(status, 'color_temp') else 4000
            }
        else:
            last_power_state[dev_id] = False
            status_cache[dev_id] = {'success': False, 'error': 'Disconnected'}
            
    while True:
        time.sleep(2)
        for dev_id, light in managers.items():
            # Skip polling if a user action happened in the last 3 seconds
            if time.time() - last_action_time.get(dev_id, 0) < 3:
                continue
            status = light.get_status()
            if status:
                was_on = last_power_state.get(dev_id, None)
                is_on = status.is_on
                last_power_state[dev_id] = is_on
                
                # Check for physical or external power-on event
                if was_on is False and is_on is True:
                    settings = load_timer_settings()
                    cfg = get_device_timer_config(settings, dev_id)
                    if cfg.get('pending_restore'):
                        logging.info(f"[{dev_id}] Detected lamp turned ON with pending restore. Applying work mode...")
                        try:
                            presets = load_presets()
                            work_preset = next((p for p in presets if p.get('name', '').strip().lower() in ['work', '工作']), None)
                            if not work_preset and presets:
                                work_preset = presets[0]
                            target_brightness = int(work_preset.get('brightness', 100)) if work_preset else 100
                            target_ct = int(work_preset.get('color_temp', 4200)) if work_preset else 4200
                            
                            time.sleep(0.3)
                            light.set_brightness(target_brightness, transition=500)
                            light.set_color_temp(target_ct, transition=500)
                            status.brightness = target_brightness
                            status.color_temp = target_ct
                        except Exception as ex:
                            logging.error(f"[{dev_id}] Failed to restore work mode on turn-on: {ex}")
                        finally:
                            cfg['pending_restore'] = False
                            settings[dev_id] = cfg
                            save_timer_settings(settings)

                status_cache[dev_id] = {
                    'success': True,
                    'is_on': status.is_on,
                    'brightness': status.brightness,
                    'color_temp': status.color_temp if hasattr(status, 'color_temp') else 4000
                }
            else:
                last_power_state[dev_id] = False
                status_cache[dev_id] = {'success': False, 'error': 'Disconnected'}

threading.Thread(target=poll_device_status, daemon=True).start()

@app.route('/')
def index():
    current_settings = load_timer_settings()
    devices_for_template = []
    for dev in devices_config:
        d = dict(dev)
        cfg = get_device_timer_config(current_settings, dev['id'])
        d['timer_mins'] = cfg['minutes']
        d['restore_work_mode'] = cfg['restore_work_mode']
        devices_for_template.append(d)
    return render_template('index.html', devices=devices_for_template)

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
    return jsonify(status_cache)

@app.route('/api/status/<device_id>', methods=['GET'])
def get_status(device_id):
    if device_id not in managers:
        return jsonify({'success': False, 'error': 'Device not found'})
    return jsonify(status_cache.get(device_id, {'success': False, 'error': 'Disconnected'}))

@app.route('/api/toggle/<device_id>', methods=['POST'])
def toggle(device_id):
    if device_id not in managers:
        return jsonify({'success': False, 'error': 'Device not found'})
    
    # Optimistically flip cache state FIRST
    if device_id in status_cache and status_cache[device_id].get('success'):
        status_cache[device_id]['is_on'] = not status_cache[device_id]['is_on']
    
    last_action_time[device_id] = time.time()
    managers[device_id].toggle()
    
    return jsonify(status_cache.get(device_id, {'success': False, 'error': 'Disconnected'}))

@app.route('/api/brightness/<device_id>', methods=['POST'])
def set_brightness(device_id):
    if device_id not in managers:
        return jsonify({'success': False, 'error': 'Device not found'})
    data = request.json
    val = data.get('value', 50)
    managers[device_id].set_brightness(int(val))
    last_action_time[device_id] = time.time()
    
    if device_id in status_cache and status_cache[device_id].get('success'):
        status_cache[device_id]['brightness'] = int(val)
        
    return jsonify({'success': True})

@app.route('/api/colortemp/<device_id>', methods=['POST'])
def set_colortemp(device_id):
    if device_id not in managers:
        return jsonify({'success': False, 'error': 'Device not found'})
    data = request.json
    val = data.get('value', 4000)
    managers[device_id].set_color_temp(int(val))
    last_action_time[device_id] = time.time()
    
    if device_id in status_cache and status_cache[device_id].get('success'):
        status_cache[device_id]['color_temp'] = int(val)
        
    return jsonify({'success': True})

QUICK_MODES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'quick_modes.json')

def load_presets():
    if not os.path.exists(QUICK_MODES_FILE):
        example_file = QUICK_MODES_FILE.replace('quick_modes.json', 'quick_modes.example.json')
        try:
            with open(example_file, 'r', encoding='utf-8') as f:
                default_presets = json.load(f)
        except Exception:
            default_presets = []
        save_presets(default_presets)
        return default_presets
    try:
        with open(QUICK_MODES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_presets(presets):
    try:
        dir_name = os.path.dirname(QUICK_MODES_FILE)
        fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix='quick_modes_', suffix='.tmp')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(presets, f, indent=4)
        os.replace(temp_path, QUICK_MODES_FILE)
    except Exception as e:
        logging.error(f"Failed to save quick_modes.json: {e}")

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
        existing_ids = {p['id'] for p in presets}
        while True:
            saved_id = str(uuid.uuid4())[:8]
            if saved_id not in existing_ids:
                break
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
        data = request.json or {}
        action = data.get('action')
        settings = load_timer_settings()
        cfg = get_device_timer_config(settings, device_id)
        if action == 'start':
            mins = max(1, min(120, int(data.get('minutes', scheduler.timer_duration_mins))))
            scheduler.start_timer(mins)
            cfg['minutes'] = mins
            settings[device_id] = cfg
            save_timer_settings(settings)
        elif action == 'set_duration':
            mins = max(1, min(120, int(data.get('minutes', 15))))
            scheduler.set_duration(mins)
            cfg['minutes'] = mins
            settings[device_id] = cfg
            save_timer_settings(settings)
        elif action == 'set_restore_work_mode':
            enabled = bool(data.get('enabled', True))
            scheduler.set_restore_work_mode(enabled)
            cfg['restore_work_mode'] = enabled
            settings[device_id] = cfg
            save_timer_settings(settings)
        elif action == 'stop':
            scheduler.stop_timer()
        return jsonify({'success': True, 'status': scheduler.get_timer_status()})
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
