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

After the service starts, access `http://localhost:<PORT>` (or your server's LAN IP:`<PORT>`) in your browser to start using it!
*(Note: `<PORT>` is the port number you configured in the `.env` file; if not configured, it defaults to port 5000.)*


> **⚖️ Disclaimer**
> This project is a third-party local control panel and is not an official product of Yeelight or Xiaomi. This project achieves compatible control solely based on officially public LAN protocols and does not provide any related services of official applications.
