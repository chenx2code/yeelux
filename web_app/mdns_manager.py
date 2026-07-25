import os
import sys
import platform
import socket
import threading
import time
from zeroconf import ServiceInfo, Zeroconf

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            device_ip = os.getenv('MI_DEVICE_IP')
            if device_ip:
                s.connect((device_ip, 80))
            else:
                s.connect(("224.0.0.251", 5353))
            local_ip = s.getsockname()[0]
        except Exception:
            try:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            except Exception:
                local_ip = socket.gethostbyname(socket.gethostname())
        finally:
            s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

class MDNSWatchdog:
    def __init__(self, port):
        self.port = port
        self.env_name = os.getenv('MDNS_NAME', 'yeelux').strip().lower()
        self.zeroconf_instance = None
        self.current_ip = None
        self.running = False
        self._first_boot = False
        
        if self.env_name in ['false', 'disabled', '0']:
            print("💡 [mDNS] Service manually disabled via environment variables.")
            return

        if sys.platform == 'win32':
            print("💡 [mDNS] Native Windows environment detected, disabling mDNS to avoid conflicts.")
            return
        
        release = platform.uname().release.lower()
        if 'microsoft' in release or 'wsl' in release:
            print("💡 [mDNS] WSL virtual network detected, disabling mDNS.")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._watch, daemon=True)
        self.thread.start()
        
    def _watch(self):
        use_passive = False
        netlink_socket = None
        
        # Attempt to use OS-level passive event listening (Linux Native)
        if sys.platform == 'linux':
            try:
                # AF_NETLINK, SOCK_RAW, NETLINK_ROUTE (0)
                netlink_socket = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, getattr(socket, 'NETLINK_ROUTE', 0))
                # Bind to RTMGRP_IPV4_IFADDR (0x10) to listen for IPv4 address changes
                netlink_socket.bind((0, 0x10))
                netlink_socket.settimeout(2.0) # Wake up every 2s to check self.running
                use_passive = True
                print("💡 [mDNS] Native OS event-driven networking enabled (Passive Mode).")
            except Exception:
                if netlink_socket:
                    netlink_socket.close()
                netlink_socket = None

        if not use_passive:
            print("💡 [mDNS] Native event listening unavailable (e.g., Sandbox/Termux). Using 3m Polling Mode.")

        while self.running:
            if use_passive:
                try:
                    # Block until a network interface event happens!
                    netlink_socket.recv(65535)
                    # Event received! We don't parse the complex Netlink binary struct, just trigger a re-check
                    new_ip = get_lan_ip()
                    if new_ip != self.current_ip:
                        self._update_mdns(new_ip)
                    time.sleep(2) # Debounce rapid interface flapping
                except socket.timeout:
                    # Normal timeout, just lets the loop check self.running
                    continue
                except Exception as e:
                    print(f"⚠️ [mDNS] Passive monitor failed ({e}), falling back to Polling Mode.")
                    use_passive = False
            else:
                # Active Polling Fallback
                new_ip = get_lan_ip()
                if new_ip != self.current_ip:
                    self._update_mdns(new_ip)
                
                # Sleep for 3m (180s) but check self.running every 1s
                for _ in range(180):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        if netlink_socket:
            netlink_socket.close()
            
    def _update_mdns(self, new_ip):
        if self.zeroconf_instance:
            print(f"🔄 [mDNS] IP changed from {self.current_ip} to {new_ip}. Restarting broadcast...")
            self.zeroconf_instance.close()
            self.zeroconf_instance = None
            
        self.current_ip = new_ip
        print(f"🔍 [mDNS] Detected local IP for broadcast: {new_ip}")
        if new_ip.startswith("127."):
            print("⚠️ [mDNS] Warning: Broadcasting localhost (127.0.0.1). This means other devices might try to connect to themselves!")
            
        try:
            info = ServiceInfo(
                "_http._tcp.local.",
                f"{self.env_name}._http._tcp.local.",
                addresses=[socket.inet_aton(new_ip)],
                port=self.port,
                properties={"desc": "Yeelux Smart Lamp Control"},
                server=f"{self.env_name}.local.",
            )
            self.zeroconf_instance = Zeroconf(interfaces=[new_ip])
            self.zeroconf_instance.register_service(info)
            if not self._first_boot:
                print(f"🚀 [mDNS] Magic broadcast started! Local network access: http://{self.env_name}.local:{self.port}")
                self._first_boot = True
        except Exception as e:
            print(f"⚠️ [mDNS] Failed to start broadcast: {e}")
            
    def close(self):
        self.running = False
        if self.zeroconf_instance:
            self.zeroconf_instance.close()
