import time
import threading
import logging

class LightScheduler:
    def __init__(self, light_manager):
        self.light = light_manager
        
        # Timer (Sleep Timer) State
        self.timer_active = False
        self.timer_end_time = 0
        
        # Focus Mode (Pomodoro) State
        self.focus_active = False
        self.focus_state = 'idle' # 'idle', 'working', 'resting'
        self.focus_end_time = 0
        self.focus_work_duration = 45 * 60  # seconds
        self.focus_rest_duration = 10 * 60  # seconds
        self.focus_saved_brightness = 50
        self.focus_saved_ct = 4000
        
        # Start daemon thread
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def start_timer(self, minutes):
        self.timer_active = True
        self.timer_end_time = time.time() + (minutes * 60)
        logging.info(f"[{self.light.name}] Sleep timer started: turning off in {minutes} minutes")

    def stop_timer(self):
        self.timer_active = False
        logging.info(f"[{self.light.name}] Sleep timer stopped")

    def get_timer_status(self):
        if not self.timer_active:
            return {'active': False, 'remaining_seconds': 0}
        rem = int(self.timer_end_time - time.time())
        if rem <= 0:
            return {'active': False, 'remaining_seconds': 0}
        return {'active': True, 'remaining_seconds': rem}

    def start_focus(self, work_mins=45, rest_mins=10):
        # Save current light state before starting focus
        status = self.light.get_status()
        if status:
            self.focus_saved_brightness = status.brightness
            self.focus_saved_ct = status.color_temp if hasattr(status, 'color_temp') else 4000
            if not status.is_on:
                self.light.turn_on()
        
        self.focus_work_duration = work_mins * 60
        self.focus_rest_duration = rest_mins * 60
        
        self.focus_active = True
        self.focus_state = 'working'
        self.focus_end_time = time.time() + self.focus_work_duration
        logging.info(f"[{self.light.name}] Focus mode started: Work {work_mins} mins, Rest {rest_mins} mins")

    def stop_focus(self):
        self.focus_active = False
        self.focus_state = 'idle'
        logging.info(f"[{self.light.name}] Focus mode stopped")

    def get_focus_status(self):
        if not self.focus_active:
            return {'active': False, 'state': 'idle', 'remaining_seconds': 0}
        rem = int(self.focus_end_time - time.time())
        return {
            'active': True,
            'state': self.focus_state,
            'remaining_seconds': max(0, rem),
            'work_mins': int(self.focus_work_duration / 60),
            'rest_mins': int(self.focus_rest_duration / 60)
        }

    def _loop(self):
        while True:
            now = time.time()
            
            # Process Timer
            if self.timer_active and now >= self.timer_end_time:
                logging.info(f"[{self.light.name}] Timer ended, turning off light")
                self.light.turn_off()
                self.timer_active = False
            
            # Process Focus Mode
            if self.focus_active:
                if now >= self.focus_end_time:
                    try:
                        if self.focus_state == 'working':
                            # Work period ended, start resting
                            logging.info(f"[{self.light.name}] Focus period ended, preparing to rest")
                            self.light.blink(2)
                            time.sleep(1) # wait for blink to finish
                            # Enter eye-protection rest mode: very warm light, lowest brightness
                            self.light.set_brightness(1)
                            self.light.set_color_temp(2600)
                            
                            self.focus_state = 'resting'
                            self.focus_end_time = time.time() + self.focus_rest_duration
                            
                        elif self.focus_state == 'resting':
                            # Rest period ended, start working
                            logging.info(f"[{self.light.name}] Rest period ended, preparing to work")
                            self.light.blink(2)
                            time.sleep(1)
                            # Restore working brightness and color temperature
                            self.light.set_brightness(self.focus_saved_brightness)
                            self.light.set_color_temp(self.focus_saved_ct)
                            
                            self.focus_state = 'working'
                            self.focus_end_time = time.time() + self.focus_work_duration
                    except Exception as e:
                        logging.error(f"[{self.light.name}] Failed to transition focus state: {e}")
            
            time.sleep(1)
