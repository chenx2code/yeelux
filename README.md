# YeeLux - Smart Light Controller

[中文](README_zh.md) | English

This is an open-source Local Area Network (LAN) control panel designed specifically for **Yeelight (and Mi Home) smart lights**, built on top of `python-miio`.
It requires no public internet connection or official apps, communicating directly with devices on your local network with millisecond-level response latency.

## ✨ Features
- ⏱️ **Sleep Timer**: One-click countdown timer to automatically turn off the light.
- 🍅 **Pomodoro / Focus Mode**: Customize work and rest durations. When a work session ends, the light will blink to notify you and automatically switch to an eye-protection dim and warm mode. When the rest session ends, it blinks again and restores the bright working light.

## 💡 Compatibility
Thanks to the underlying `python-miio` universal protocol library, this project is theoretically compatible with the vast majority of Yeelight products that support "LAN Control".

## 🛠️ Installation

### 1. Basic Dependencies
Ensure you have Python 3.8+ installed on your computer or server.
After cloning this repository, install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Device Configuration (devices.json)
This project supports controlling multiple smart lights across your home. Copy `devices.example.json` in the project root directory and rename it to `devices.json`, then fill in the IP and Token for all your devices:
```json
[
  {
    "id": "light_1",
    "name": "Study Desk Lamp",
    "ip": "192.168.1.X",
    "token": "your_32_character_token"
  },
  {
    "id": "light_2",
    "name": "Bedroom Ceiling Light",
    "ip": "192.168.1.Y",
    "token": "your_32_character_token_2"
  }
]
```
*(You can also copy `.env.example` in the root directory and rename it to `.env` to modify and specify configurations like the running port. This is optional.)*

> **🔑 About getting the Yeelight Token:**
> This project uses pure LAN UDP protocol for communication, which requires your device's 32-character Token for authentication.
> We recommend using the third-party extractor tool written by Piotr Machowski:
> 👉 [Xiaomi Cloud Tokens Extractor (GitHub)](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor)
>
> Run the extractor according to the official instructions of that project, and it will automatically list the IP and Token for all smart devices under your account. Once obtained, fill them into the `devices.json` file mentioned above. (Note: This project does not contain any third-party scripts involving Xiaomi cloud logins.)

### 3. Run the Service

**Method 1: Run locally with Python**
```bash
python web_app/app.py
```

**Method 2: Deploy with Docker (Recommended)**
This project supports one-click deployment using Docker. Ensure you have `docker` and `docker compose` installed, and have created the `devices.json` file in the root directory.
```bash
docker compose up -d
```
*(Note: If you run Docker on a native Linux system like a NAS or Raspberry Pi, it is highly recommended to modify `docker-compose.yml` to enable `network_mode: "host"` to support UDP auto-discovery. Windows/Mac users should keep the default configuration.)*

After the service starts, you can access it in your browser using `http://localhost:<PORT>` or your server's LAN IP (e.g., `http://192.168.1.x:<PORT>`).
*(Note: `<PORT>` is the port number you configured in the `.env` file, defaulting to 5000.)*

---

### 🌐 LAN Geek Access: Zero-Config mDNS Domain Broadcast

To provide the ultimate smart home experience, this project features a built-in **mDNS (Multicast DNS) LAN broadcast**, powered by `zeroconf`.

**1. Core Advantages and Solved Pain Points**
In a home network, the router's DHCP mechanism can cause the server's IP address to change. When the IP changes, your saved bookmarks become invalid, and you have to constantly check the new IP, which is extremely tedious.
The mDNS feature perfectly solves this: it automatically broadcasts a fixed domain name to your entire local network. You **never have to memorize boring IP addresses again**. From any browser connected to the same Wi-Fi, simply type the domain 👉 **`http://yeelux.local:5000`** and the control panel will permanently and reliably appear!

**2. Supported Environments and Configurations**
- **Supported Environments**: Native physical Linux machines (like Raspberry Pi, Ubuntu servers), NAS devices, and Android phones (Termux).
- **What users need to do**:
  - **If running directly with Python**: No configuration needed. The code automatically broadcasts `yeelux.local` out of the box.
  - **If deploying with Docker**: You **MUST** modify the `docker-compose.yml` file: **comment out the `ports` lines and uncomment `network_mode: "host"`**. This binds the container directly to the host's physical network adapter, transmitting the mDNS broadcast to the entire LAN.
  - *(Advanced)* **If running multiple instances in the same home**: To prevent hostname conflicts, you need to forcefully override the name by adding a line to the respective `.env` file (e.g., `MDNS_NAME=yeelux-bedroom`). The domain for that machine will instantly change to `http://yeelux-bedroom.local:5000`.

**3. Unsupported Environments and Workarounds**
- **Unsupported Environments**: Native Windows, native Mac, Windows WSL virtual machines, and Docker Desktop on Windows/Mac. These environments have underlying virtual NAT network isolation, which blocks mDNS multicast packets from reaching the physical LAN.
- **What users need to do**:
  - The code automatically detects these isolated virtual environments at startup and **silently disables** the mDNS feature to prevent the program from crashing due to network conflicts.
  - You don't need to change any code. If deploying with Docker, please **keep the default `ports: ["5000:5000"]` configuration untouched** in `docker-compose.yml`.
  - You must access the control panel the traditional way, by entering `http://localhost:5000` or the server's actual LAN IP address in your browser.

---

### 📱 Deploying on an Android Phone (Termux)

If you want to turn an Android phone into a 24/7 micro-server, deploying with **Termux** is an excellent choice. Since this project uses `cryptography` (which relies on Rust), compiling it directly on a phone will likely fail. Please follow these specific steps to avoid common pitfalls:

**1. Install basic environment and pre-compiled packages**
Run the following commands in Termux to use the system's high-performance pre-compiled packages, bypassing Rust compilation errors:
```bash
pkg update && pkg upgrade -y
pkg install python git clang make python-cryptography rust openssl -y
```

**2. Clone the project and create a virtual environment using system packages**
You **must** add the `--system-site-packages` parameter here so the virtual environment can "borrow" the pre-compiled `python-cryptography` package we just installed.
```bash
git clone https://github.com/yourusername/yeelux.git
cd yeelux
python -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```

**3. Configure and bypass Android dynamic linking bugs to start**
Due to a dynamic linking bug (`PyBaseObject_Type`) in the latest Termux Python 3.13, we must use `LD_PRELOAD` to inject the core library during startup:
```bash
cp devices.example.json devices.json
nano devices.json  # Fill in your real lamp IP and Token

# Inject the dynamic library and start the magic service!
LD_PRELOAD=$PREFIX/lib/libpython3.13.so python web_app/app.py
```

> **⚠️ CRITICAL: Keeping Termux alive in the background:**
> 1. Pull down the phone's notification shade and click **Acquire wakelock** on the Termux notification to prevent the CPU from sleeping.
> 2. Go to the Android system settings and change Termux's battery optimization to **"Unrestricted"**.
> 3. **Lock** the Termux app in the recent apps (multitasking) menu to prevent it from being killed by the system cleaner.

---

> **⚖️ Disclaimer**
> This project is a third-party local control panel and is not an official product of Yeelight or Xiaomi. This project achieves compatible control solely based on officially public LAN protocols and does not provide any related services of official applications.
