# YeeLux - 智能灯具局域网中枢 (Smart Light Controller)

中文 | [English](README.md)

这是一个基于 `python-miio` 开发，专为 **Yeelight（及米家）系列智能灯具** 打造的开源局域网控制面板。
无需依赖公网连接或官方 App，完全在局域网内与设备直连通信，响应延迟在毫秒级别。

## 1. 特性 (Features)
- ⏱️ **睡眠定时**: 一键设置倒计时，到时自动关灯。
- 🍅 **番茄钟/专注模式**: 自定义工作与休息时间。工作结束时，台灯会自动闪烁提醒，并自动切入护眼昏黄模式；休息结束再次闪烁并恢复工作明亮灯光。
## 2. 兼容性说明 (Compatibility)
得益于底层的 `python-miio` 通用协议库，本项目理论上兼容市面上绝大多数支持“局域网控制”的 Yeelight 灯具产品。

## 3. 安装说明 (Installation)

### 3.1 获取基础依赖
确保你的电脑或服务器上安装了 Python 3.8+ 环境。
克隆本仓库后，安装相关依赖包：
```bash
pip install -r requirements.txt
```

### 3.2 配置设备 (devices.json)
本项目支持控制全屋的多个智能灯具。在项目根目录复制 `devices.example.json` 并重命名为 `devices.json`，然后填入你所有设备的 IP 和 Token：
```json
[
  {
    "id": "lamp_1",
    "name": "工作台灯",
    "ip": "192.168.1.X",
    "token": "你的32位Token"
  },
  {
    "id": "lamp_2",
    "name": "卧室吸顶灯",
    "ip": "192.168.1.Y",
    "token": "你的32位Token_2"
  }
]
```
*(你还可以复制根目录下的 `.env.example` 并重命名为 `.env`，在里面修改和指定运行端口等配置，非必填。)*

> **🔑 关于如何获取 Yeelight Token：**
> 本项目基于纯局域网 UDP 协议通信，需要你设备的 32 位 Token 才能进行身份验证。
> 推荐使用 Piotr Machowski 编写的第三方提取工具：
> 👉 [Xiaomi Cloud Tokens Extractor (GitHub)](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor)
>
> 按照该项目的官方指引运行提取器，即可自动列出账号下所有智能设备的 IP 和 Token。获取后填入上方的 `devices.json` 文件即可。（注：本项目无内置任何涉及小米云端登录的第三方脚本。）

### 3.3 启动服务 (Run)

**方式一：使用 Python 本地运行**
```bash
python web_app/app.py
```

**方式二：使用 Docker 部署 (推荐)**
本项目支持使用 Docker 一键部署。请确保你的环境中已安装 `docker` 和 `docker compose`，并且已经在根目录下创建好了 `devices.json` 文件。
```bash
docker compose up -d
```
*(注：如果你的 Docker 运行在真实的 Linux 系统如 NAS/树莓派 上，强烈建议修改 `docker-compose.yml` 启用 `network_mode: "host"`，以支持局域网设备 UDP 自动发现功能。Windows/Mac 用户保持默认配置即可。)*

服务启动后，你可以在浏览器中访问本机的 `http://localhost:<PORT>` 或服务器的局域网 IP (例如 `http://192.168.1.x:<PORT>`) 开始使用。
*(注：`<PORT>` 为 `.env` 中配置的端口号，默认 5000。)*

---

### 3.4 🌐 局域网极客访问：静态 IP (推荐)

为了获得最稳定、无延迟的智能家居体验，**强烈建议为部署 Yeelux 服务的设备分配静态 IP**。

在家庭局域网中，路由器的 DHCP 机制可能会导致服务器的 IP 地址发生变化。一旦 IP 变化，你之前保存在手机或电脑上的书签就会失效。

**最佳实践**：
1. 登录你的家用路由器后台。
2. 找到“DHCP 静态 IP 分配”或“IP/MAC 绑定”功能。
3. 将运行本服务的设备（如旧手机、树莓派）绑定一个固定的 IP（例如 `192.168.1.100`）。
4. 在手机或电脑浏览器中直接将 `http://192.168.1.100:5000` 添加为书签或桌面快捷方式。

这样不仅告别了 mDNS 带来的休眠转圈延迟，还能确保服务永远一触即达。

---

### 3.5 📱 部署在安卓手机 (Termux) 上

如果你想把安卓手机当成 24 小时运行的微型服务器，使用 **Termux** 部署是一个极佳的选择。由于本项目使用了 `cryptography`（底层依赖 Rust），在手机上直接编译极大概率会报错。请严格按照以下**避坑步骤**进行部署：

**1. 安装基础环境与预编译包**
在 Termux 中执行以下命令，直接使用系统提供的高性能预编译包，绕过 Rust 编译报错：
```bash
pkg update && pkg upgrade -y
pkg install python git clang make python-cryptography rust openssl -y
```

**2. 克隆项目并使用系统包创建虚拟环境**
这里**必须**加上 `--system-site-packages` 参数，让虚拟环境能够“借用”上一步安装好的 `python-cryptography` 预编译包。
```bash
git clone https://github.com/您的用户名/yeelux.git
cd yeelux
python -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```

**3. 配置与解决 Android 底层 Bug 启动**
由于最新的 Termux Python 3.13 存在 `PyBaseObject_Type` 动态链接 Bug，我们必须使用 `LD_PRELOAD` 进行底层库注入启动：
```bash
cp devices.example.json devices.json
nano devices.json  # 填入你真实的台灯 IP 和 Token

# 注入动态库并启动魔法服务！
LD_PRELOAD=$PREFIX/lib/libpython3.13.so python web_app/app.py
```

> **⚠️ 保持后台运行的极其重要提醒：**
> 1. 下拉手机通知栏，在 Termux 通知上点击 **Acquire wakelock** (获取唤醒锁)，防止息屏后 CPU 休眠导致断网。
> 2. 去手机系统设置中，将 Termux 的电池优化策略改为 **“无限制”**。
> 3. 在多任务界面给 Termux **加锁**，防止被系统清理。

---

> **⚖️ 免责声明 (Disclaimer)**
> 本项目为第三方本地控制面板，非 Yeelight 或小米官方出品。本项目仅基于官方公开的局域网协议实现兼容控制，不提供任何官方应用的相关服务。
