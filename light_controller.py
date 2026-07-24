import time
import logging
from miio import Yeelight

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LightManager:
    """Core controller class for Yeelight Desk Light"""
    def __init__(self, ip: str, token: str, name: str = "Unknown Light"):
        self.ip = ip
        self.token = token
        self.name = f"{name} - {ip}"
        self.light = None
        self._connect()

    def _connect(self):
        try:
            self.light = Yeelight(self.ip, self.token)
            status = self.light.status()
            logging.info(f"[{self.name}] Successfully connected. Status: {'ON' if status.is_on else 'OFF'}")
            return True
        except Exception as e:
            logging.error(f"[{self.name}] Failed to connect to light: {e}")
            self.light = None
            return False

    def is_connected(self):
        return self.light is not None

    def get_status(self):
        if not self.is_connected():
            return None
        try:
            return self.light.status()
        except Exception as e:
            logging.error(f"[{self.name}] Failed to get status: {e}")
            self._connect() # Attempt to reconnect
            return None

    def turn_on(self):
        if self.is_connected():
            try:
                self.light.on()
                logging.info(f"[{self.name}] Light turned ON")
            except Exception as e:
                logging.error(f"[{self.name}] Failed to turn light ON: {e}")

    def turn_off(self):
        if self.is_connected():
            try:
                self.light.off()
                logging.info(f"[{self.name}] Light turned OFF")
            except Exception as e:
                logging.error(f"[{self.name}] Failed to turn light OFF: {e}")

    def toggle(self):
        status = self.get_status()
        if status:
            if status.is_on:
                self.turn_off()
            else:
                self.turn_on()

    def set_brightness(self, level: int):
        if self.is_connected():
            try:
                level = max(1, min(100, level))
                self.light.set_brightness(level)
                logging.info(f"[{self.name}] Light brightness set to {level}%")
            except Exception as e:
                logging.error(f"[{self.name}] Failed to set light brightness: {e}")

    def set_color_temp(self, level: int):
        if self.is_connected():
            try:
                level = max(2600, min(5000, level))
                self.light.set_color_temp(level)
                logging.info(f"[{self.name}] Light color temperature set to {level}K")
            except Exception as e:
                logging.error(f"[{self.name}] Failed to set light color temperature: {e}")

    def blink(self, count=2):
        """Make the light blink for notification"""
        if not self.is_connected():
            return
        status = self.get_status()
        if not status: return
        
        was_on = status.is_on
        original_brightness = status.brightness

        try:
            # If the light is off, turn it on first
            if not was_on:
                self.light.on()
                time.sleep(0.5)

            # Execute blinking
            for _ in range(count):
                self.light.set_brightness(1)
                time.sleep(0.5)
                self.light.set_brightness(100)
                time.sleep(0.5)
            
            # Restore original state
            if not was_on:
                self.light.off()
            else:
                self.light.set_brightness(original_brightness)
                
            logging.info(f"[{self.name}] Light blinked {count} times")
        except Exception as e:
            logging.error(f"[{self.name}] Failed to blink light: {e}")

if __name__ == "__main__":
    # Test code
    from dotenv import load_dotenv
    import os
    
    # Automatically load environment variables from .env file
    load_dotenv()
    
    IP = os.getenv("YEELIGHT_IP")
    TOKEN = os.getenv("YEELIGHT_TOKEN")
    
    if not IP or not TOKEN:
        print("Error: Please create a .env file in the project root and fill in YEELIGHT_IP and YEELIGHT_TOKEN")
        exit(1)
        
    manager = LightManager(IP, TOKEN)
    
    if manager.is_connected():
        print("Preparing to execute blink test...")
        manager.blink(count=2)
